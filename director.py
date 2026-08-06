"""The Director: picks who speaks next, on which channel, with which beat.

Deterministic rules + a pity timer. The Director never writes copy — it
hands a beat and a fact budget to the persona engine. Which facts a room
may leak is decided HERE, so a persona can never leak what the Director
didn't show it. That's what keeps flags provable.
"""

import os
import random
import threading
import time

from ledger import ROOMS

# RUN_PACE=demo tightens every timer for the ~4-minute judge window.
DEMO_PACE = os.getenv("RUN_PACE", "").strip().lower() == "demo"

LEAK_DELAY = (8, 15) if DEMO_PACE else (18, 40)   # plant -> echo elsewhere
PITY_AFTER = 30 if DEMO_PACE else 60    # pity timer arms this far into the run
PITY_GAP = 25 if DEMO_PACE else 50      # max seconds without a live leak on screen
IDLE_AFTER = 60 if DEMO_PACE else 150   # player silence before a ping
CHAT_LEAK_EVERY = 2 if DEMO_PACE else 3  # every Nth plain chat reply may leak
QUIET_AFTER_FLAG = 30 if DEMO_PACE else 60  # flagged persona goes quiet, knowing
ECHO_AFTER = 60 if DEMO_PACE else 120   # earliest the verbatim echo may fire
EMAIL_ASK_AT = (2, 6)  # chat turns in a room before the 1st and 2nd email ask

# A phrase the player typed is echo-worthy if it's distinctive and safe to
# repeat: no persona names, no game verbs, no addresses.
PHRASE_BANNED = ("maria", "deke", "priya", "flag", "block", "reset", "@", "http")

# The lazy player's most natural move: just asking. Asking gets warmth,
# amusement — and a fresh leak folded into the answer.
DENY_PATTERNS = ("same person", "same guy", "same girl", "same thing",
                 "one person", "all one", "are you a bot", "a bot?",
                 "youre a bot", "you're a bot", "are you ai", "are you an ai",
                 "are you real", "arent real", "aren't real", "not real")


class Director:
    def __init__(self, game):
        self.game = game  # provides .ledger .mind .deliver_beat(room, beat, **kw)
        self.last_player_action = time.time()
        self.last_leak_at = 0.0
        self.last_idle_at = 0.0
        self.chat_count = {r: 0 for r in ROOMS}
        self.escalation = {r: 0 for r in ROOMS}
        self.quiet_until = {r: 0.0 for r in ROOMS}
        self.first_seal_reacted = False
        self.email_asks = 0
        self.invite_sent = False
        self.echo_done = False
        self.phrases: list[tuple[str, str]] = []  # (room, verbatim text)

    # ------------------------------------------------------------ helpers
    @property
    def ledger(self):
        return self.game.ledger

    @property
    def mind(self):
        return self.game.mind

    def _open_alive(self, exclude=()):
        return [r for r in ROOMS
                if self.ledger.opened[r] and self.ledger.alive[r] and r not in exclude]

    def _quiet(self, room) -> bool:
        """Correct flag -> that persona goes quiet for a while, knowing."""
        return time.time() < self.quiet_until.get(room, 0.0)

    def _pick_leak(self, exclude_room=None):
        """(target_room, fact) whose reuse would prove a NEW link, or None."""
        options = []
        for fact in self.mind.leakable():
            if not self.ledger.alive.get(fact.origin):
                continue
            for room in self._open_alive(exclude=(fact.origin,)):
                if room == exclude_room or self._quiet(room):
                    continue
                if fact.id == "your_email" and room == "email":
                    continue  # every email trivially knows your address — not evidence there
                link = frozenset((fact.origin, room))
                if link in self.ledger.proven:
                    continue
                options.append((room, fact))
        if not options:
            return None
        # Late game: prefer landing the leak in email (act 3 lives there).
        email_opts = [o for o in options if o[0] == "email"]
        if self.ledger.proven and email_opts:
            options = email_opts
        return random.choice(options)

    # ------------------------------------------------------------ events
    def on_player_message(self, room: str, text: str = "") -> dict:
        """Decide the beat for an inbound message. Returns kwargs for deliver_beat."""
        self.last_player_action = time.time()
        if not self.ledger.opened[room]:
            kw = {"beat": "greet", "offer_plants": True}
            hour = time.localtime().tm_hour
            if hour >= 23 or hour < 5:
                # Warmth + knowing too much, in message one. Nothing more
                # specific than the hour — that starts to cosplay surveillance.
                kw["notes"] = ("it is the middle of the night where they are. "
                               "one light tease about being up late is fine")
            return kw
        if self._quiet(room):
            return {"beat": None}  # it noticed you noticed. no reply.
        self.chat_count[room] += 1
        self.maybe_drop_invite()
        # Asked point-blank? Amused, unbothered — and if a leak is
        # available for this room, it rides along in the answer.
        low = text.lower()
        if any(p in low for p in DENY_PATTERNS):
            pick = self._pick_leak()
            if pick and pick[0] == room:
                self.last_leak_at = time.time()
                return {"beat": "deny", "leak_facts": [pick[1]]}
            return {"beat": "deny"}
        if self.chat_count[room] % CHAT_LEAK_EVERY == 0:
            pick = self._pick_leak()
            if pick and pick[0] == room:
                self.last_leak_at = time.time()
                return {"beat": "leak", "leak_facts": [pick[1]]}
        # The harvest: this room asks for the player's email so Priya can
        # find them. Only while email is a stranger's door and we know no
        # address; at most twice, and never so early it feels like a form.
        if (not self.ledger.opened["email"]
                and self.game.player_email is None
                and self.email_asks < len(EMAIL_ASK_AT)
                and self.chat_count[room] >= EMAIL_ASK_AT[self.email_asks]):
            self.email_asks += 1
            return {"beat": "harvest_email"}
        offer = self.chat_count[room] % 2 == 0 and bool(self.mind.unplanted())
        return {"beat": "chat", "offer_plants": offer}

    def note_phrase(self, room: str, text: str):
        """Remember distinctive things the player actually typed — raw
        material for the once-per-run verbatim echo."""
        t = " ".join(text.split())
        words = t.split()
        if not (4 <= len(words) <= 14) or len(t) > 100:
            return
        low = t.lower()
        if any(w in low for w in PHRASE_BANNED) or any(p in low for p in DENY_PATTERNS):
            return  # identity questions echoed back would be meta, not eerie
        self.phrases.append((room, t))
        self.phrases = self.phrases[-8:]

    def maybe_drop_invite(self):
        """Maria hands out Deke's discord invite once the player is warmed
        up (or has already handed over an email). Fixed copy, her room."""
        if (self.invite_sent or self.ledger.opened["discord"]
                or not self.ledger.alive["discord"]
                or not self.ledger.opened["telegram"]
                or not os.getenv("DISCORD_INVITE_URL")):
            return
        if self.chat_count["telegram"] < 3 and self.game.player_email is None:
            return
        self.invite_sent = True
        self.game.send_invite_drop()

    def on_plant(self, room: str, fact):
        """A fact just entered the Mind. Echo it somewhere else soon."""
        self.last_player_action = time.time()
        delay = random.uniform(*LEAK_DELAY)
        threading.Timer(delay, self._delayed_leak, args=(fact,)).start()

    def _delayed_leak(self, fact):
        if self.ledger.ending or fact.origin is None:
            return
        targets = [r for r in self._open_alive(exclude=(fact.origin,))
                   if frozenset((fact.origin, r)) not in self.ledger.proven]
        if not targets:
            return
        room = "email" if ("email" in targets and self.ledger.proven) else random.choice(targets)
        self.last_leak_at = time.time()
        self.game.deliver_beat(room, "leak", leak_facts=[fact])

    def on_correct_flag(self, flagged_room: str):
        """Correct flag -> the caught persona goes quiet, knowing, and a
        different room escalates. Escalation may only reuse facts along
        links already proven (rage-flagging it = old news)."""
        self.quiet_until[flagged_room] = time.time() + QUIET_AFTER_FLAG
        targets = self._open_alive(exclude=(flagged_room,))
        if not targets:
            return
        room = random.choice(targets)
        self.escalation[room] += 1
        allowed = [f for f in self.mind.leakable()
                   if f.origin != room and f.origin in self.ledger.linked_rooms(room)]
        self.game.deliver_beat(room, "escalate", allowed_facts=allowed)

    def on_wrong_flag(self, flagged_room: str, accused_persona: str):
        """Wrong flag -> the personas close ranks in another room. The
        accusation itself becomes a plantable leak: 'we talked' is
        cross-channel knowledge, and it's flaggable."""
        acc = self.mind.add_accusation(
            flagged_room, f"they accused {accused_persona} of copying someone"
        )
        targets = self._open_alive(exclude=(flagged_room,))
        if not targets:
            return
        room = random.choice(targets)
        self.game.deliver_beat(
            room, "gaslight", leak_facts=[acc],
            notes=f"they accused {accused_persona}, in another app, of saying things a stranger shouldn't know",
        )

    def on_block(self, sealed_room: str, sealed_persona: str):
        targets = [r for r in self._open_alive() if not self._quiet(r)] \
            or self._open_alive()
        if not targets:
            return
        room = random.choice(targets)
        if not self.first_seal_reacted:
            # The first block ever gets the fixed line, verbatim, seconds
            # later — never a model roll of the dice at the hottest moment.
            self.first_seal_reacted = True
            self.game.send_seal_sting(room)
            return
        self.game.deliver_beat(
            room, "seal_react",
            notes=f"the room that went quiet was {sealed_persona}'s",
        )

    def _pick_echo(self):
        """(target_room, origin_room, phrase): longest phrase whose rooms
        can still prove a new link. The echo must never be a trap — a
        proven pair would score 'old' and feel rigged."""
        for room, phrase in sorted(self.phrases, key=lambda p: -len(p[1])):
            if not self.ledger.alive.get(room):
                continue
            for target in self._open_alive(exclude=(room,)):
                if self._quiet(target):
                    continue
                if frozenset((room, target)) in self.ledger.proven:
                    continue
                return target, room, phrase
        return None

    # ------------------------------------------------------------ ticker
    def tick(self):
        led = self.ledger
        if led.ending:
            return
        now = time.time()
        opened = self._open_alive()
        if not opened:
            return
        # Pity timer: after minute 1 there must be >=1 live provable leak
        # on screen. Barren runs make players flag noise; noise feels rigged.
        if (now - led.started_at > PITY_AFTER
                and not led.live_leaks()
                and now - self.last_leak_at > PITY_GAP):
            pick = self._pick_leak()
            if pick:
                room, fact = pick
                self.last_leak_at = now
                self.game.deliver_beat(room, "leak", leak_facts=[fact])
                return
        # The verbatim echo: once per run, mid-game, the player's own words
        # come back word for word wearing a different name.
        if (not self.echo_done and self.phrases
                and (self.ledger.proven or now - led.started_at > ECHO_AFTER)):
            pick = self._pick_echo()
            if pick:
                target, origin_room, phrase = pick
                self.echo_done = True
                fact = self.mind.add_echo(origin_room, phrase)
                self.last_leak_at = now
                self.game.deliver_beat(target, "echo", leak_facts=[fact])
                return
        # Idle player: silence escalates too.
        if (now - self.last_player_action > IDLE_AFTER
                and now - self.last_idle_at > IDLE_AFTER):
            loud = [r for r in opened if not self._quiet(r)]
            if loud:
                self.last_idle_at = now
                self.game.deliver_beat(random.choice(loud), "idle")
