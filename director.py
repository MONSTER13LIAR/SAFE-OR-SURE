"""The Director: picks who speaks next, on which channel, with which beat.

Deterministic rules + a pity timer. The Director never writes copy — it
hands a beat and a fact budget to the persona engine. Which facts a room
may leak is decided HERE, so a persona can never leak what the Director
didn't show it. That's what keeps flags provable.

It owns no difficulty numbers of its own: every delay, every density,
every "how obvious is this leak" comes off the current `levels.Level`.
One Director serves one level; the Session builds a new one per rung.
"""

import os
import random
import threading
import time

import levels
from ledger import ROOMS

# Playtest 2026-08-12: the middle of a run was dead air. A planted fact
# could sit unused for 40s and only every third reply could carry a leak,
# so a player who did everything right still spent minutes watching
# nothing happen. Density IS the motive — the per-level leak timings in
# levels.py are the answer to "why would they keep playing".
IDLE_AFTER = 60 if levels.DEMO_PACE else 120   # player silence before a ping
IDLE_PING_MAX = 2   # then the game goes dormant — never texts a gone player forever
QUIET_AFTER_FLAG = 20 if levels.DEMO_PACE else 35  # flagged persona goes quiet, knowing
ECHO_AFTER = 50 if levels.DEMO_PACE else 90   # earliest the verbatim echo may fire
# The hook. Opening a second door is the moment the game becomes a game,
# and it used to be followed by a stranger saying a bland hello while the
# leak arrived whenever the dice said so. Now the room you just opened
# knows something within seconds — every run, guaranteed.
OPEN_HOOK = (5, 9)
# The clock speaks twice. Both from the game, never from a persona: a
# person announcing your deadline is the fiction admitting it's a game.
CLOCK_WARNINGS = (60, 20)
# The "up late?" beat needs a wall clock, and a host box runs on UTC. Env
# vars on a host can silently not apply (a blueprint edit doesn't reach a
# running service), so the offset lives here instead: India has no DST, so
# a fixed offset is exact and needs no tz database either.
LOCAL_UTC_OFFSET = float(os.getenv("GAME_UTC_OFFSET", "5.5"))


def local_hour(now: float | None = None) -> int:
    """The player's likely hour of day. Their zone is unknowable; this is
    the audience's, and nothing more specific than the hour is ever used."""
    return int(((now if now is not None else time.time()) / 3600
                + LOCAL_UTC_OFFSET) % 24)


# The asks come early on purpose: until a second room is open, no leak can
# exist and no flag can be right, so a player alone in room one is holding
# a game that has not started. Everything that opens a door is act zero.
EMAIL_ASK_AT = (1, 4)   # chat turns in a room before the 1st and 2nd email ask
HANDLE_ASK_AT = (3, 8)  # ...and before asking which name to look for on discord
# Which door each room hands out, in the order it tries them. Whoever the
# player found first becomes their guide into the rooms they haven't opened.
# "email" is the last resort in each list — the inbox is supposed to arrive
# by Priya finding you after you hand over the address, and that beat is
# the thesis; it is only handed over outright once the asks have failed.
DOORS_FROM = {"telegram": ("discord", "email"),
              "discord": ("telegram", "email"),
              "email": ("telegram", "discord")}

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
    def __init__(self, run):
        self.run = run  # provides .ledger .mind .deliver_beat(room, beat, **kw)
        self.last_player_action = time.time()
        self.last_leak_at = 0.0
        self.last_idle_at = 0.0
        self.last_room = "telegram"
        self.chat_count = {r: 0 for r in ROOMS}
        self.escalation = {r: 0 for r in ROOMS}
        self.quiet_until = {r: 0.0 for r in ROOMS}
        self.first_seal_reacted = False
        self.idle_pings = 0
        self.email_asks = 0
        self.handle_asks = 0
        # How many of the player's next messages may be read as the answer
        # to "whats your discord name". Outside that window their words are
        # just words — see Session._scan_for_handle.
        self.handle_answer_window = 0
        self.doors_dropped: set[str] = set()
        self.doors_nudged: set[str] = set()
        self.echo_done = False
        self.warned: set[int] = set()
        self.phrases: list[tuple[str, str]] = []  # (room, verbatim text)

    # ------------------------------------------------------------ helpers
    @property
    def ledger(self):
        return self.run.ledger

    @property
    def mind(self):
        return self.run.mind

    @property
    def level(self):
        return self.run.ledger.level

    def _open_alive(self, exclude=()):
        return [r for r in ROOMS
                if self.ledger.opened[r] and self.ledger.alive[r] and r not in exclude]

    def _quiet(self, room) -> bool:
        """Correct flag -> that persona goes quiet for a while, knowing."""
        return time.time() < self.quiet_until.get(room, 0.0)

    def note_player_action(self, room: str | None = None):
        """Any tap or text: the player is here. Re-arms the idle pings."""
        self.last_player_action = time.time()
        self.idle_pings = 0
        if room:
            self.last_room = room

    def on_send_failed(self, beat: str, leak_facts=()):
        """A beat died before reaching the screen. Un-consume the one-shot
        state, or the run silently loses its echo and the pity timer sits
        satisfied by a leak nobody saw."""
        if beat == "echo":
            self.echo_done = False
        if leak_facts:
            self.last_leak_at = 0.0

    def _pick_leak(self, exclude_room=None, only_room=None):
        """(target_room, fact) whose reuse would prove a NEW link, or None."""
        if not self.level.leaks:
            return None  # the last level does not slip
        options = []
        for fact in self.mind.leakable():
            if not self.ledger.alive.get(fact.origin):
                continue
            for room in self._open_alive(exclude=(fact.origin,)):
                if room == exclude_room or self._quiet(room):
                    continue
                if only_room and room != only_room:
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

    def _pick_decoy(self) -> str | None:
        """Flag-bait. A persona talks about something the player has NOT
        given anyone — as a thing out of its own life. It reads exactly
        like a leak ("wait, did I tell somebody about the printer?") and it
        is provably not one: no fact id is ever shown to the model for
        these, so none can appear in facts_used, so the Ledger scores a
        flag on it as noise. Fair, and mechanically airtight.

        Decoys are the whole difficulty curve. A level with none is a
        reading test; a level full of them is a test of what you actually
        said and to whom, which is the game this wants to be.

        On the last level the pool widens to everything the player gave
        away on the way up. It spends level 10 knowing all of it out loud
        and never once giving a receipt for any of it."""
        pool = [f.text for f in self.mind.unplanted() if not f.retired]
        if not self.level.leaks:
            pool = list(self.run.known) + pool
        return random.choice(pool) if pool else None

    def _leak_notes(self) -> str:
        return self.level.style

    # ------------------------------------------------------------ events
    def on_player_message(self, room: str, text: str = "") -> dict:
        """Decide the beat for an inbound message. Returns kwargs for deliver_beat."""
        self.note_player_action(room)
        if not self.ledger.opened[room]:
            kw = {"beat": "greet", "offer_plants": True}
            hour = local_hour()
            if hour >= 23 or hour < 5:
                # Warmth + knowing too much, in message one. Nothing more
                # specific than the hour — that starts to cosplay surveillance.
                kw["notes"] = ("it is the middle of the night where they are. "
                               "one light tease about being up late is fine")
            return kw
        if self._quiet(room):
            return {"beat": None}  # it noticed you noticed. no reply.
        self.chat_count[room] += 1
        self.maybe_drop_doors(room)
        # Asked point-blank? Amused, unbothered — and if a leak is
        # available for this room, it rides along in the answer.
        low = text.lower()
        if any(p in low for p in DENY_PATTERNS):
            pick = self._pick_leak(only_room=room)
            if pick:
                self.last_leak_at = time.time()
                return {"beat": "deny", "leak_facts": [pick[1]],
                        "notes": self._leak_notes()}
            return {"beat": "deny"}
        if self.level.leak_every and self.chat_count[room] % self.level.leak_every == 0:
            pick = self._pick_leak(only_room=room)
            if pick:
                self.last_leak_at = time.time()
                return {"beat": "leak", "leak_facts": [pick[1]],
                        "notes": self._leak_notes()}
        # No leak available for this room this turn. On the harder levels
        # the silence is filled with something that looks exactly like one.
        if random.random() < self.level.decoy_chance:
            bait = self._pick_decoy()
            if bait:
                return {"beat": "decoy", "notes": bait}
        # The harvest: this room asks for the player's email so Priya can
        # find them. Only while email is a stranger's door and we know no
        # address; at most twice, and never so early it feels like a form.
        if (not self.ledger.opened["email"]
                and self.run.player_email is None
                and self.email_asks < len(EMAIL_ASK_AT)
                and self.chat_count[room] >= EMAIL_ASK_AT[self.email_asks]):
            self.email_asks += 1
            return {"beat": "harvest_email"}
        # And the other missing door: Deke can't be messaged first, so the
        # only way to know the stranger who DMs him is the player's own
        # word for who they are over there.
        if (room != "discord"
                and not self.ledger.opened["discord"]
                and self.ledger.alive["discord"]
                and "discord" in self.doors_dropped
                and not self.run.expect.get("discord")
                and self.handle_asks < len(HANDLE_ASK_AT)
                and self.chat_count[room] >= HANDLE_ASK_AT[self.handle_asks]):
            self.handle_asks += 1
            self.handle_answer_window = 2   # this reply, or the one after it
            return {"beat": "harvest_handle"}
        # Plants are the only move a player has before a second room opens.
        # Early on they come with every reply — the first run must never
        # reach a turn where the screen offers nothing to do — and settle
        # into every other turn once there's a game to play.
        offer = bool(self.mind.unplanted()) and (
            len(self.mind.planted()) < 3 or self.chat_count[room] % 2 == 0)
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

    def maybe_drop_doors(self, room):
        """Whichever room the player found first hands out the ones they
        haven't opened — the conversation is the onboarding, and any room
        can be the way in. Once each, warmed up, fixed copy."""
        if self.ledger.ending or not self.ledger.opened[room]:
            return
        if self.chat_count[room] < 1 and self.run.player_email is None:
            return
        for target in DOORS_FROM.get(room, ()):
            if (target in self.doors_dropped or self.ledger.opened[target]
                    or not self.ledger.alive[target]
                    or not self.run.door_url(target)):
                continue
            if (target == "email" and self.email_asks < len(EMAIL_ASK_AT)
                    and self.run.player_email is None):
                continue  # let it ask first; the address is the fallback
                          # (but on a second run we already have it, and the
                          #  asks never fire, so the door must not be stuck)
            self.doors_dropped.add(target)
            self.run.send_door_drop(room, target)
            return

    def on_room_opened(self, room: str):
        """A second (or third) door just opened. Within seconds the person
        behind it knows something the player only ever told somebody else.

        This is the hook, and before it was scheduled it was a dice roll:
        a stranger could open Discord, get a bland hello, and never see why
        this was a game. Now every run gets its moment, on the clock."""
        if len(self._open_alive()) < 2 or not self.level.leaks:
            return
        self._schedule_leak(random.uniform(*OPEN_HOOK), only_room=room)

    def _schedule_leak(self, delay: float, fact=None, only_room=None):
        # The epoch rides along with every other deferred beat in this
        # game, and it has to ride along with this one too: a run that is
        # swept or restarted while the timer sleeps must not wake up and
        # message somebody whose game no longer exists.
        threading.Timer(delay, self._delayed_leak,
                        args=(fact, only_room, self.run.epoch)).start()

    def on_plant(self, room: str, fact):
        """A fact just entered the Mind. Echo it somewhere else soon."""
        self.note_player_action(room)
        if self.level.leaks:
            self._schedule_leak(random.uniform(*self.level.leak_delay), fact=fact)

    def _delayed_leak(self, fact=None, only_room=None, epoch=None):
        if self.run.director is not self or self.run.dead:
            return  # a reset, a level change or a sweep happened mid-sleep
        if epoch is not None and self.run.epoch != epoch:
            return
        if self.ledger.ending or not self.level.leaks:
            return
        if fact is None:
            pick = self._pick_leak(only_room=only_room)
            if pick is None:
                return
            room, fact = pick
        else:
            if fact.origin is None:
                return
            targets = [r for r in self._open_alive(exclude=(fact.origin,))
                       if frozenset((fact.origin, r)) not in self.ledger.proven
                       and (not only_room or r == only_room)]
            if not targets:
                return
            room = ("email" if ("email" in targets and self.ledger.proven)
                    else random.choice(targets))
        self.last_leak_at = time.time()
        self.run.deliver_beat(room, "leak", leak_facts=[fact],
                              notes=self._leak_notes())

    def on_correct_flag(self, flagged_room: str):
        """Correct flag -> the caught persona goes quiet, knowing, and a
        different room escalates. Escalation may only reuse facts along
        links already proven (rage-flagging it = old news)."""
        self.quiet_until[flagged_room] = time.time() + QUIET_AFTER_FLAG
        # A player with a proven link who never opened a room is in an
        # unwinnable game and doesn't know it. Re-drop that door, once, at
        # the moment they're most invested.
        for shut in ROOMS:
            if (shut in self.doors_dropped and shut not in self.doors_nudged
                    and not self.ledger.opened[shut] and self.ledger.alive[shut]
                    and self.run.door_url(shut)):
                for host in self._open_alive():
                    if shut in DOORS_FROM.get(host, ()):
                        self.doors_nudged.add(shut)
                        self.run.send_door_drop(host, shut, nudge=True)
                        break
                break
        targets = self._open_alive(exclude=(flagged_room,))
        if not targets:
            return
        room = random.choice(targets)
        self.escalation[room] += 1
        allowed = [f for f in self.mind.leakable()
                   if f.origin != room and f.origin in self.ledger.linked_rooms(room)]
        self.run.deliver_beat(room, "escalate", allowed_facts=allowed)

    def on_wrong_flag(self, flagged_room: str, accused_persona: str):
        """Wrong flag -> the personas close ranks in another room. 'We
        talked about you' is itself cross-channel knowledge, so the
        accusation is minted as a fact and flagging it scores.

        But only ever along a link the player already proved. Left
        unrestricted this was a way to WIN by playing badly: flag nothing
        in particular, get gaslit somewhere else, flag the gaslight, and
        collect a link you never planted a single fact to earn. Now it
        lands on a proven pair — so it reads exactly as eerie, it burns a
        flag if you rage-flag it, and it can never manufacture progress.
        Same rule the escalate beat has always followed."""
        targets = self._open_alive(exclude=(flagged_room,))
        if not targets:
            return
        notes = (f"they accused {accused_persona}, in another app, of saying "
                 "things a stranger shouldn't know")
        proven = self.ledger.linked_rooms(flagged_room)
        landable = [r for r in targets if r in proven]
        if not self.level.leaks or not landable:
            self.run.deliver_beat(random.choice(targets), "gaslight", notes=notes)
            return
        acc = self.mind.add_accusation(
            flagged_room, f"they accused {accused_persona} of copying someone"
        )
        self.run.deliver_beat(random.choice(landable), "gaslight",
                              leak_facts=[acc], notes=notes)

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
            self.run.send_seal_sting(room)
            return
        self.run.deliver_beat(
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
        # The clock. Two warnings, then the level is over — that pressure
        # is the reason the middle of a run has a shape at all.
        left = led.time_left()
        if left is not None:
            if left <= 0:
                self.run.on_time_up()
                return
            for mark in CLOCK_WARNINGS:
                if left <= mark and mark not in self.warned:
                    self.warned.add(mark)
                    self.run.send_clock_warning(self.last_room, left, mark)
                    break
        # Pity timer: after the level warms up there must be >=1 live
        # provable leak on screen. Barren runs make players flag noise;
        # noise feels rigged.
        if (self.level.pity_gap
                and now - led.started_at > self.level.pity_gap
                and not led.live_leaks()
                and now - self.last_leak_at > self.level.pity_gap):
            pick = self._pick_leak()
            if pick:
                room, fact = pick
                self.last_leak_at = now
                self.run.deliver_beat(room, "leak", leak_facts=[fact],
                                      notes=self._leak_notes())
                return
        # The verbatim echo: once per level, mid-game, the player's own
        # words come back word for word wearing a different name.
        if (self.level.leaks and not self.echo_done and self.phrases
                and (self.ledger.proven or now - led.started_at > ECHO_AFTER)):
            pick = self._pick_echo()
            if pick:
                target, origin_room, phrase = pick
                self.echo_done = True
                fact = self.mind.add_echo(origin_room, phrase)
                self.last_leak_at = now
                self.run.deliver_beat(target, "echo", leak_facts=[fact])
                return
        # Idle player: silence escalates too — but only twice. Past that
        # they're gone, and a game that keeps texting a gone person is
        # exactly the optics this game can't have.
        if (self.idle_pings < IDLE_PING_MAX
                and now - self.last_player_action > IDLE_AFTER
                and now - self.last_idle_at > IDLE_AFTER):
            loud = [r for r in opened if not self._quiet(r)]
            if loud:
                self.last_idle_at = now
                self.idle_pings += 1
                self.run.deliver_beat(random.choice(loud), "idle")
