"""SAFE OR SURE — three channels, one shared handler, one Mind.

Run:  .venv/bin/python game.py

The handler never branches on message.channel. Rooms are keyed by
connection_id; the transport IS the map.
"""

import os
import random
import re
import threading
import time

from caspian_sdk import CommClient
from caspian_sdk import blocks as b

import deck
import personas
from director import DEMO_PACE, Director
from ledger import ROOMS, Ledger
from mind import Mind

PERSONA_BY_ROOM = {"telegram": "maria", "discord": "deke", "email": "priya"}
BLOCK_POLL_SECONDS = (3, 6, 9, 13)  # still `queued` after the last poll => sealed
# Cold open: say hi to one stranger and the other two find you. Seconds
# between the player's first hello and each unprompted first contact.
COLD_OPEN_DELAY = (8, 15) if DEMO_PACE else (15, 30)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Abandoned mid-run / ended-and-ignored: quietly free the seat. Demo pace
# shrinks it — a judge's drive-by "hi" must not hold the door for 15 min.
DORMANT_RESET = 3 * 60 if DEMO_PACE else 15 * 60
ENDED_RESET = 2 * 60 if DEMO_PACE else 10 * 60


class Game:
    def __init__(self, client: CommClient):
        self.client = client
        self.lock = threading.RLock()
        self.room_locks = {r: threading.Lock() for r in ROOMS}
        self.conn_to_room: dict[str, str] = {}
        self.conversations: dict[str, str] = {}   # room -> conversation_id
        self.game_email: str | None = None        # our own address, never harvested
        self.telegram_url = os.getenv("TELEGRAM_BOT_URL") or None  # the front page's first door
        self.epoch = 0            # bumped on reset; sleeping threads check it
        self.best_named: list[float] = []  # fastest NAMED times, seconds, this boot
        self.reset()

    def reset(self):
        with self.lock:
            self.epoch += 1
            self.owners: dict[str, str] = {}  # room -> sender key; one run, one player
            # The conversation map dies with the run: the next player's
            # messages (and case file) must never route into the previous
            # player's threads.
            self.conversations = {}
            self.ended_at: float | None = None
            self.run_duration: float | None = None
            self.mind = Mind()
            self.ledger = Ledger(self.mind)
            self.director = Director(self)
            self.history: dict[str, list[dict]] = {r: [] for r in ROOMS}
            self.ended_notified = False
            self.cold_open_started = False
            self.cold_opened: set[str] = set()
            # The player's email: from .env for the builder, or harvested
            # in-game when they answer Maria's ask. Cold-open + case-file target.
            self.player_email = os.getenv("PLAYER_EMAIL") or None
            self.harvest_room: str | None = None
            self.harvest_times: dict[str, float] = {}

    def room_conn(self) -> dict[str, str]:
        return {room: conn for conn, room in self.conn_to_room.items()}

    # ------------------------------------------------------------ delivery
    def deliver_beat(self, room, beat, **kw):
        """Generate + send off the listen thread; per-room lock keeps each
        room's turns ordered while a slow model in one room never blocks
        the others."""
        threading.Thread(target=self._deliver_now,
                         args=(room, beat, self.epoch),
                         kwargs=kw, daemon=True).start()

    def _deliver_now(self, room, beat, epoch, leak_facts=(), allowed_facts=(),
                     new_fact=None, notes="", offer_plants=False, inbound=None):
        with self.room_locks[room]:
            self._generate_and_send(room, beat, epoch, leak_facts,
                                    allowed_facts, new_fact, notes,
                                    offer_plants, inbound)

    def _generate_and_send(self, room, beat, epoch, leak_facts, allowed_facts,
                           new_fact, notes, offer_plants, inbound):
        led = self.ledger
        if self.epoch != epoch or led.ending or not led.alive.get(room):
            return
        if beat != "greet" and not led.opened[room]:
            return
        persona = PERSONA_BY_ROOM[room]
        own = [f for f in self.mind.planted(room)
               if f is not new_fact and not f.verbatim]
        turn = None
        for attempt in (1, 2):
            try:
                turn = personas.persona_turn(
                    persona, self.history[room], beat,
                    own_facts=own, leak_facts=leak_facts,
                    allowed_facts=allowed_facts, new_fact=new_fact, notes=notes,
                )
                break
            except Exception as e:
                print(f"!! persona call failed ({room}/{beat}, try {attempt}): {e}")
                if attempt == 1:
                    time.sleep(2)
        if turn is None:
            # Model down twice. Silence during a run reads as a broken game —
            # load-bearing beats fall back to fixed lines; the rest skip.
            turn = self._fallback_turn(persona, beat, leak_facts)
            if turn is None:
                if self.epoch == epoch:
                    self.director.on_send_failed(beat, leak_facts)
                return
            print(f"-> [{room}/{beat}] fallback line")
        if beat == "echo" and leak_facts:
            # The echo is only the echo if it's word for word. If the model
            # paraphrased, the bare phrase alone is the better message anyway.
            quote = leak_facts[0]
            if quote.value and quote.value.lower() not in turn.message.lower():
                turn.message = quote.value
            if quote.id not in turn.facts_used:
                turn.facts_used.append(quote.id)
        parts = None
        if beat != "echo" and room != "email":
            # People double-text. Line breaks arrive as separate messages,
            # staggered — on escalate, that burst is the wordless invitation
            # to hit Block. Email stays one message: nobody double-emails.
            # Overflow folds into the last text instead of being dropped:
            # the Ledger must only ever score words that actually ship.
            cap = 3 if beat == "escalate" else 2
            parts = [p.strip() for p in turn.message.split("\n") if p.strip()]
            if len(parts) > cap:
                parts = parts[:cap - 1] + [" ".join(parts[cap - 1:])]
            turn.message = "\n".join(parts) if parts else turn.message
        with self.lock:
            if self.epoch != epoch:
                return  # reset while the model was thinking: dead run's words
            rec = led.record_turn(room, turn.message, turn.facts_used)
            hist_entry = {"who": "you", "text": turn.message}
            self.history[room].append(hist_entry)
        buttons = [{"label": deck.FLAG_LABEL, "value": f"flag:{rec.id}"}]
        if offer_plants:
            pool = self.mind.unplanted()
            for fact in random.sample(pool, min(2, len(pool))):
                buttons.append({"label": deck.PLANT_PREFIX + fact.label,
                                "value": f"plant:{fact.id}"})
            buttons.append({"label": deck.DEFLECT_LABEL, "value": "deflect"})
        visible = turn.message
        delivered_part = False
        if parts and len(parts) > 1:
            for p in parts[:-1]:
                if self.epoch != epoch:
                    return
                delivered_part = self.send_text(room, p) or delivered_part
                time.sleep(random.uniform(1.0, 2.0))
            visible = parts[-1]
        if self.epoch != epoch:
            return
        payload = [b.text(visible), b.buttons(buttons), b.text(led.hud())]
        ok, sent = self._send(room, payload, inbound)
        if not ok and not delivered_part:
            # Nothing reached the screen: forget the turn — and tell the
            # Director, so a lost echo/leak can fire again later.
            with self.lock:
                led.turns.pop(rec.id, None)
                if hist_entry in self.history[room]:
                    self.history[room].remove(hist_entry)
            if self.epoch == epoch:
                self.director.on_send_failed(beat, leak_facts)
            return
        if not ok:
            # The leading texts landed, the final one didn't: the words are
            # on the player's screen, so the receipt must stand ('flag' by
            # text still scores it). Only the button watch is lost.
            print(f"!! final part failed ({room}/{beat}); turn {rec.id} kept")
            return
        if sent:
            rec.message_id = sent.get("id") or (sent.get("message") or {}).get("id")
            self._watch_for_block(room, rec.message_id)
        print(f"-> [{room}/{beat}] {persona}: {turn.message!r} facts={turn.facts_used}")

    def _fallback_turn(self, persona, beat, leak_facts):
        if beat == "greet":
            return personas.PersonaTurn(
                message=deck.FALLBACK_GREET[persona], facts_used=[])
        if beat == "escalate":
            return personas.PersonaTurn(
                message=deck.FALLBACK_ESCALATE[persona], facts_used=[])
        if beat == "echo" and leak_facts and leak_facts[0].value:
            # The bare phrase IS the message; the echo fixup fills the rest.
            return personas.PersonaTurn(message=leak_facts[0].value,
                                        facts_used=[leak_facts[0].id])
        return None

    def _send(self, room, payload_blocks, inbound=None):
        """(delivered, response). delivered=False means the player never got
        it — no conversation yet, or the gateway threw."""
        try:
            if inbound is not None:
                return True, inbound.reply(blocks=payload_blocks)
            conv = self.conversations.get(room)
            if conv:
                return True, self.client.send_message(conv, blocks=payload_blocks)
        except Exception as e:
            print(f"!! send failed ({room}): {e}")
        return False, None

    def send_text(self, room, text) -> bool:
        try:
            conv = self.conversations.get(room)
            if conv:
                self.client.send_message(conv, text=text)
                return True
        except Exception as e:
            print(f"!! send failed ({room}): {e}")
        return False

    # ------------------------------------------------------------ blocking
    def _watch_for_block(self, room, message_id):
        if not message_id or room == "email":
            return  # email has no block button. That's the thesis.
        epoch = self.epoch

        def watch():
            conv = self.conversations.get(room)
            if not conv:
                return
            for _ in range(4):
                time.sleep(3.5)
                if self.epoch != epoch:
                    return  # reset mid-watch: never seal a fresh run's room
                try:
                    msgs = self.client.list_messages(conv)
                except Exception:
                    return
                status = next((m.get("status") for m in msgs if m.get("id") == message_id), None)
                if status not in ("queued", "pending"):
                    return  # delivered (or unknowable) — room is open
            self._room_sealed(room)

        threading.Thread(target=watch, daemon=True).start()

    def _room_sealed(self, room):
        with self.lock:
            if not self.ledger.alive.get(room) or self.ledger.ending:
                return
            result = self.ledger.block(room)
        print(f"** room sealed: {room}")
        if result.get("ending"):
            self.finish()
        else:
            self.director.on_block(room, PERSONA_BY_ROOM[room].title())

    # ------------------------------------------------------------ cold open
    def cold_open_room(self, room, recipient):
        """One unprompted first contact, after a human-feeling delay. The
        recipient is always a handle the player registered or handed over
        themselves — that's the consent mechanism."""
        with self.lock:
            if (room in self.cold_opened or self.ledger.opened[room]
                    or not self.ledger.alive[room]):
                return
            self.cold_opened.add(room)
        epoch = self.epoch

        def run():
            time.sleep(random.uniform(*COLD_OPEN_DELAY))
            with self.lock:
                if (self.epoch != epoch or self.ledger.ending
                        or self.ledger.opened[room] or not self.ledger.alive[room]):
                    return
                line = deck.COLD_OPEN[room]
                self.history[room].append({"who": "you", "text": line})
            conn = self.room_conn().get(room)
            if not conn:
                return
            try:
                self.client.initiate(conn, recipient, line)
                if room == "email" and self.harvest_room:
                    self.harvest_times["used"] = time.time()
                print(f"-> [{room}/cold_open] {line!r}")
            except Exception as e:
                print(f"!! cold open failed ({room}): {e}")

        threading.Thread(target=run, daemon=True).start()

    def maybe_cold_open(self, entry_room):
        """First hello anywhere -> any stranger whose door we already know
        finds YOU. Telegram can't initiate cold, so Maria's room is the
        entry door; Priya's door usually arrives later, via the harvest."""
        with self.lock:
            if self.cold_open_started:
                return
            self.cold_open_started = True
        if entry_room != "discord" and os.getenv("PLAYER_DISCORD_ID"):
            self.cold_open_room("discord", os.environ["PLAYER_DISCORD_ID"])
        if entry_room != "email" and self.player_email:
            self.cold_open_room("email", self.player_email)

    # ------------------------------------------------------------ the harvest
    def _scan_sender(self, room, message):
        """Mint what the channel itself just leaked about the player:
        display name, sending address. Provenance = the room that showed it."""
        s = getattr(message, "sender", None) or {}
        name = (s.get("name") or "").strip()
        addr = (s.get("address") or "").strip()
        if room == "email" and "@" in addr:
            self._learn_email(room, addr)
        if name and len(name) >= 2:
            with self.lock:
                fact = self.mind.get("your_name")
                if fact is None:
                    self.mind.add_meta("your_name", deck.META_NAME_LABEL,
                                       deck.META_NAME_TEXT.format(v=name),
                                       room, name)
                elif (not fact.retired and fact.origin != room
                      and fact.value and fact.value.lower() == name.lower()):
                    # Same display name visible in a second room: no longer
                    # unique knowledge, no longer fair evidence.
                    self.mind.retire("your_name")

    def _scan_for_email(self, room, text):
        """The player answers Maria's ask. Only harvested after an ask has
        actually happened — a pasted third-party address in idle chat must
        never make the game email a stranger."""
        if room == "email" or self.director.email_asks == 0:
            return
        m = EMAIL_RE.search(text)
        if not m:
            return
        addr = m.group(0)
        if self.game_email and addr.lower() == self.game_email.lower():
            return
        if addr.lower().endswith("trycaspianai.com"):
            return
        self._learn_email(room, addr)

    def _learn_email(self, room, addr):
        with self.lock:
            minted = self.mind.add_meta("your_email", deck.META_EMAIL_LABEL,
                                        deck.META_EMAIL_TEXT.format(v=addr),
                                        room, addr)
            if minted and room != "email":
                self.harvest_room = room
                self.harvest_times["gave"] = time.time()
            if self.player_email is None:
                self.player_email = addr
        if room != "email" and not self.ledger.opened["email"]:
            self.cold_open_room("email", addr)
        self.director.maybe_drop_invite()

    def send_invite_drop(self, nudge=False):
        """Maria's follow-up text with Deke's door. Fixed copy, delayed a
        few seconds so it lands like an afterthought, not a system message.
        The nudge is the second, firmer drop — for a player who proved a
        link but still hasn't opened Deke's room, without which the run
        can't be won."""
        url = os.getenv("DISCORD_INVITE_URL")
        if not url or not self.conversations.get("telegram"):
            return
        line = (deck.INVITE_NUDGE if nudge else deck.INVITE_DROP).format(url=url)
        epoch = self.epoch

        def run():
            time.sleep(random.uniform(4, 8))
            with self.lock:
                if (self.epoch != epoch or self.ledger.ending
                        or not self.ledger.alive["telegram"]):
                    return
                self.history["telegram"].append({"who": "you", "text": line})
            self.send_text("telegram", line)
            print(f"-> [telegram/invite_drop] {line!r}")

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------ fixed beats
    def send_seal_sting(self, room):
        """First block ever: the fixed line, verbatim, two seconds later."""
        epoch = self.epoch

        def run():
            time.sleep(2)
            with self.lock:
                if (self.epoch != epoch or self.ledger.ending
                        or not self.ledger.alive.get(room)):
                    return
                self.history[room].append({"who": "you", "text": deck.SEAL_FIRST})
            self.send_text(room, deck.SEAL_FIRST)
            print(f"-> [{room}/seal_sting] {deck.SEAL_FIRST!r}")

        threading.Thread(target=run, daemon=True).start()

    def _broadcast(self, pairs):
        """Send (room, text) pairs released together so they land as one
        simultaneous buzz — the masks drop all at once, not one at a time."""
        pairs = [p for p in pairs if self.conversations.get(p[0])]
        if not pairs:
            return
        barrier = threading.Barrier(len(pairs))

        def send(room, text):
            try:
                barrier.wait(timeout=5)
            except threading.BrokenBarrierError:
                pass
            self.send_text(room, text)

        threads = [threading.Thread(target=send, args=p, daemon=True) for p in pairs]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

    # ------------------------------------------------------------ inbound
    def _sender_key(self, message) -> str:
        s = getattr(message, "sender", None) or {}
        key = s.get("address") or s.get("username") or s.get("id") or ""
        return str(key).lower() or str(message.conversation_id)

    def on_message(self, message):
        room = self.conn_to_room.get(message.connection_id)
        if room is None:
            return
        # One run, one player. A second person mid-run must never hijack
        # the conversation map or the owner's Mind — they get the busy
        # line and the run stays whole. (After an ending anyone may reset.)
        key = self._sender_key(message)
        with self.lock:
            owner = self.owners.get(room)
            ending = self.ledger.ending
            run_live = any(self.ledger.opened.values()) and not ending
            busy = owner is not None and key != owner and not ending
            # An unopened room is still the run's room. Email is gated the
            # moment we know the player's address — the game email is in
            # the README, and a stranger walking in through it mid-run
            # would be minted straight into the owner's Mind.
            if (not busy and owner is None and run_live and room == "email"
                    and self.player_email
                    and key != self.player_email.lower()):
                busy = True
        if busy:
            print(f"<- [{room}] busy: {key!r} knocked during the owner's run")
            try:
                message.reply(text=deck.BUSY)
            except Exception:
                pass
            return
        self.conversations[room] = message.conversation_id
        text = (message.text or "").strip()
        print(f"<- [{room}] {text!r}")

        if text.lower() in ("reset", "/reset"):
            # Mid-run, only someone already in the run may pull the plug —
            # a stranger's 'reset' to an untouched room must not kill a
            # live game.
            with self.lock:
                allowed = (self.ledger.ending
                           or not any(self.ledger.opened.values())
                           or self.owners.get(room) == key)
            if not allowed:
                message.reply(text=deck.BUSY)
                return
            self.reset()
            message.reply(text=deck.RESET_OK)
            return
        if text.lower() == "/start":
            # Telegram sends this when the player taps Start. After a run
            # it reads as "again"; mid-run it's just a hello — either way
            # the literal slash-command must never reach a persona.
            if self.ledger.ending:
                self.reset()
                message.reply(text=deck.RESET_OK)
                return
            text = "hi"
        if self.ledger.ending:
            message.reply(text=deck.AFTER_END)
            return
        if text.lower() in ("flag", "⚑"):  # text fallback (email has no buttons everywhere)
            latest = self.ledger.latest_turn(room)
            if latest:
                self._handle_flag(room, latest.id, inbound=message)
            return

        # Only now does the sender own the door: commands, ended-run
        # bounces and dead-end flags above never latch a room shut on
        # the real player.
        with self.lock:
            self.owners.setdefault(room, key)
        self._scan_sender(room, message)
        self._scan_for_email(room, text)
        self.director.note_phrase(room, text)
        self.history[room].append({"who": "them", "text": text})
        decision = self.director.on_player_message(room, text)
        if decision["beat"] is None:
            return  # flagged persona stays quiet, knowing
        first_contact = not self.ledger.opened[room]
        if first_contact:
            if not any(self.ledger.opened.values()):
                # The clock starts at the first hello, not at boot — a game
                # that sat idle for an hour must not log a 1:03:00 run.
                self.ledger.started_at = time.time()
            self.ledger.opened[room] = True
            if room in self.cold_opened and decision["beat"] == "greet":
                # It already said hello via the cold open — don't greet twice.
                decision = {"beat": "chat", "offer_plants": True}
            self.maybe_cold_open(room)
        self.deliver_beat(room, decision["beat"],
                          leak_facts=decision.get("leak_facts", ()),
                          offer_plants=decision.get("offer_plants", False),
                          notes=decision.get("notes", ""),
                          inbound=message)

    def on_interaction(self, interaction):
        room = self.conn_to_room.get(interaction.connection_id)
        value = interaction.value or ""
        if room is None:
            return
        # Buttons outlive runs. A tap only counts if it comes from the
        # room's current conversation — anything else is a stale button
        # from a previous run or a foreign thread, and acting on it would
        # let a ghost reset, plant into, or flag the live game.
        conv = interaction.conversation_id
        with self.lock:
            cur = self.conversations.get(room)
        if cur is None or (conv and conv != cur):
            print(f"<- [{room}] stale tap {value!r} ignored")
            return
        self.director.note_player_action()
        if value == "reset":  # the [run it back] button on the case file
            print(f"<- [{room}] tap {value!r}")
            if not self.ledger.ending:
                return  # [run it back] only lives on a case file
            self.reset()
            # reset() just cleared the conversation map — answer through
            # the thread the tap came from. The gateway rejects reply()
            # on interactions, so send directly.
            try:
                self.client.send_message(conv or cur, text=deck.RESET_OK)
            except Exception as e:
                print(f"!! reset ack failed ({room}): {e}")
            return
        if self.ledger.ending:
            self.send_text(room, deck.AFTER_END)
            return
        print(f"<- [{room}] tap {value!r}")

        if value == "deflect":
            self.send_text(room, deck.DEFLECTED)
        elif value.startswith("plant:"):
            fact = self.mind.plant(value.split(":", 1)[1], room)
            if fact:
                self.director.on_plant(room, fact)
                self.deliver_beat(room, "react_plant", new_fact=fact)
        elif value.startswith("flag:"):
            self._handle_flag(room, value.split(":", 1)[1])

    def _handle_flag(self, room, turn_id, inbound=None):
        with self.lock:
            result = self.ledger.flag(turn_id)

        def answer(text):
            # Must never raise: on the run-ending flag, an exception here
            # would swallow finish() — no case file, and the seat bricks.
            body = f"{text}\n{self.ledger.hud()}"
            if inbound is not None:
                try:
                    inbound.reply(text=body)
                    return
                except Exception as e:
                    print(f"!! flag reply failed ({room}): {e}")
            self.send_text(room, body)

        verdict = result["verdict"]
        if verdict == "spent":
            answer(deck.FLAG_SPENT)
            return
        if verdict == "over":
            return
        if verdict == "link":
            a, room_b = result["links"][0]
            tmpl = deck.LINKED if len(self.ledger.proven) > 1 else deck.LINKED_FIRST
            answer(tmpl.format(a=a, b=room_b))
            if result.get("ending"):
                self.finish()
            else:
                self.director.on_correct_flag(room)
        else:  # old / noise — a wrong flag either way
            answer(deck.FLAG_OLD_NEWS if verdict == "old" else deck.FLAG_NOISE)
            if result.get("ending"):
                self.finish()
            else:
                self.director.on_wrong_flag(room, PERSONA_BY_ROOM[room].title())

    # ------------------------------------------------------------ endings
    def finish(self):
        with self.lock:
            if self.ended_notified or not self.ledger.ending:
                return
            self.ended_notified = True
            ending = self.ledger.ending
            self.ended_at = time.time()
            self.run_duration = self.ended_at - self.ledger.started_at
            if ending == "NAMED":
                self.best_named = sorted(self.best_named + [self.run_duration])[:5]
        print(f"** ENDING: {ending}")
        open_alive = [r for r in ROOMS if self.ledger.opened[r] and self.ledger.alive[r]]
        if ending == "NAMED":
            # It stops mid-sentence — shown, not told: every living room cuts
            # off an ordinary unfinished sentence at once, three seconds of
            # nothing, then the card.
            self._broadcast([(r, deck.NAMED_CUT[r]) for r in open_alive])
            time.sleep(3)
            self._broadcast([(r, deck.ENDING_NAMED) for r in open_alive])
        elif ending == "CORNERED":
            # Name, deterministically, what each block burned — the loss
            # must decode to specific choices, never to "rigged".
            body = deck.ENDING_CORNERED
            burned = [
                deck.CORNERED_BURNED.format(
                    persona=PERSONA_BY_ROOM[r].title(), fact=f.label)
                for r in ROOMS if not self.ledger.alive[r]
                for f in self.mind.planted(r)
            ]
            if burned:
                body += "\n\n" + deck.CORNERED_BURNED_HEADER + "\n" + "\n".join(burned)
            self.send_text("email", body)
        elif ending == "SWARMED":
            # The same sentence, every room, one buzz.
            self._broadcast([(r, deck.ENDING_SWARMED) for r in open_alive])
            self.send_text("email", deck.ENDING_SWARMED_CODA)
        self._send_case_file(ending)

    def _case_cover_note(self, ending, sealed):
        """Priya opens the case file in her own voice — generated post-run,
        when latency costs nothing. Gated: any failure or slop and the case
        file ships without it."""
        try:
            turn = personas.persona_turn(
                "priya", self.history["email"], "casefile",
                notes=(f"the run ended: {ending}. they used "
                       f"{6 - self.ledger.flags_left} of 6 flags and sealed "
                       f"{sealed} rooms."),
            )
            note = turn.message.strip()
            banned = ("certainly", "great question", "delve", "journey",
                      "fascinating", "watching", "always here")
            if note and len(note) <= 400 and not any(w in note.lower() for w in banned):
                return note
        except Exception as e:
            print(f"!! case cover note skipped: {e}")
        return None

    def _mmss(self, ts) -> str:
        s = max(0, int(ts - self.ledger.started_at))
        return f"{s // 60}:{s % 60:02d}"

    def _send_case_file(self, ending):
        lines = [deck.CASE_HEADER]
        if self.harvest_room and "gave" in self.harvest_times and "used" in self.harvest_times:
            lines.append(deck.CASE_HARVEST.format(
                gave=self._mmss(self.harvest_times["gave"]),
                persona=PERSONA_BY_ROOM[self.harvest_room].title(),
                used=self._mmss(self.harvest_times["used"])))
        for t in sorted(self.ledger.turns.values(), key=lambda t: t.ts):
            for fid in t.facts_used:
                fact = self.mind.get(fid)
                if fact is None or fact.origin is None or fact.origin == t.room:
                    continue
                tmpl = deck.CASE_CAUGHT if t.flag_verdict == "link" else deck.CASE_MISSED
                lines.append(tmpl.format(room=t.room, fact=fact.label,
                                         origin=fact.origin, at=self._mmss(t.ts)))
            if t.flag_verdict in ("old", "noise"):
                lines.append(deck.CASE_WRONG.format(room=t.room))
        sealed = sum(1 for r in ROOMS if not self.ledger.alive[r])

        # The portrait: what it knew about you, door by door. Deterministic.
        lines.append("")
        lines.append(deck.CASE_PORTRAIT_HEADER)
        for r in ROOMS:
            persona = PERSONA_BY_ROOM[r].title()
            facts = [f.label for f in self.mind.planted(r)]
            lines.append(
                deck.CASE_PORTRAIT_ROOM.format(room=r, persona=persona,
                                               facts=", ".join(facts))
                if facts else
                deck.CASE_PORTRAIT_NONE.format(room=r, persona=persona))

        used = 6 - self.ledger.flags_left
        # Winning gets a time on the card — the speedrun hook. Losses don't;
        # nobody brags about how fast they got cornered.
        result = ending
        if ending == "NAMED" and self.ended_at:
            result = f"{ending} in {self._mmss(self.ended_at)}"
        lines.append(deck.CASE_FOOTER.format(result=result, used=used, sealed=sealed))
        dots = self.ledger.hud().split(" · ")[0]
        lines.append("")
        lines.append(deck.SHARE_CARD.format(result=result, used=used, dots=dots))

        if note := self._case_cover_note(ending, sealed):
            lines.insert(0, note + "\n")
        body = "\n".join(lines)
        conv = self.conversations.get("email")
        if conv:
            try:
                self.client.send_message(conv, blocks=[
                    b.text(body),
                    b.buttons([{"label": deck.RUN_IT_BACK, "value": "reset"}]),
                ])
                return
            except Exception as e:
                print(f"!! case file send failed: {e}")
        # Player never opened email: the case file (the replay driver) must
        # still reach them — cold-start the thread if we know their address.
        if (addr := self.player_email) and (conn := self.room_conn().get("email")):
            try:
                self.client.initiate(conn, addr, body)
                return
            except Exception as e:
                print(f"!! case file initiate failed: {e}")
        print(body)

    # ------------------------------------------------------------ ticker
    def _maybe_expire(self):
        """Free the seat: a run abandoned mid-game, or an ended run nobody
        restarted, quietly resets so the next stranger gets a fresh game."""
        with self.lock:
            led = self.ledger
            now = time.time()
            if led.ending:
                # ended_at can be None if finish() ever died mid-flight —
                # fall back to the last action so the seat can't brick.
                end_ts = self.ended_at or self.director.last_player_action
                stale = now - end_ts > ENDED_RESET
            else:
                stale = (any(led.opened.values())
                         and now - self.director.last_player_action > DORMANT_RESET)
        if stale:
            print("** run expired — seat freed")
            self.reset()

    def start_ticker(self):
        def loop():
            while True:
                time.sleep(10)
                try:
                    self.director.tick()
                    self._maybe_expire()
                except Exception as e:
                    print(f"!! tick failed: {e}")
        threading.Thread(target=loop, daemon=True).start()

    # ------------------------------------------------------------ spectator
    def doors(self) -> dict[str, str]:
        """The public entry points, for the front page: only the rooms a
        visitor can actually open right now. A judge who lands on the URL
        should be one tap from playing, never hunting through a README."""
        offer = {
            "telegram": self.telegram_url,
            "discord": os.getenv("DISCORD_INVITE_URL"),
            "email": self.game_email,
        }
        return {room: url for room, url in offer.items() if url}

    def state_snapshot(self) -> dict:
        """What the constellation page may see: the shape of the run, never
        a word of the conversation."""
        with self.lock:
            led = self.ledger
            web = led.email_web()
            in_run = any(led.opened.values()) and not led.ending
            if led.ending and self.run_duration is not None:
                secs = int(self.run_duration)
            elif in_run:
                secs = int(time.time() - led.started_at)
            else:
                secs = None
            return {
                "rooms": [{
                    "id": r,
                    "tag": deck.ROOM_TAGS[r],
                    "persona": PERSONA_BY_ROOM[r].title(),
                    "alive": led.alive[r],
                    "opened": led.opened[r],
                    "linked": r in web and len(web) > 1,
                } for r in ROOMS],
                "links": [sorted(l) for l in led.proven],
                "flags_left": led.flags_left,
                "ending": led.ending,
                "run_seconds": secs,
                "in_run": in_run,
                "best_named": [int(t) for t in self.best_named],
                "doors": self.doors(),
            }


def telegram_bot_url(token: str) -> str | None:
    """Ask Telegram what the bot is publicly called, so the front page can
    offer its door without one more env var to fill in."""
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(
                f"https://api.telegram.org/bot{token}/getMe", timeout=10) as r:
            name = (json.load(r).get("result") or {}).get("username")
        return f"https://t.me/{name}" if name else None
    except Exception as e:
        print(f"!! telegram getMe failed: {e}")
        return None


def connect(client: CommClient, game: Game):
    email = client.connect_email(username=os.getenv("AGENT_NAME", "kernel"))
    game.conn_to_room[email["id"]] = "email"
    game.game_email = email.get("address")
    print(f"email    {email.get('address')}")

    tg_token = os.environ["TELEGRAM_BOT_TOKEN"]
    tg = client.connect_telegram(bot_token=tg_token)
    game.conn_to_room[tg["id"]] = "telegram"
    game.telegram_url = game.telegram_url or telegram_bot_url(tg_token)
    print(f"telegram {tg['id']} (Maria) {game.telegram_url or ''}")

    if token := os.getenv("DISCORD_BOT_TOKEN"):
        dc = client.connect_discord(bot_token=token)
    else:
        dc = client.get_connection(os.environ["DISCORD_CONNECTION_ID"])
    game.conn_to_room[dc["id"]] = "discord"
    print(f"discord  {dc['id']} (Deke)")


def preflight():
    """Fail with a checklist, not a KeyError traceback."""
    missing = [k for k in ("CASPIAN_API_KEY", "TELEGRAM_BOT_TOKEN")
               if not os.getenv(k)]
    if not (os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_CONNECTION_ID")):
        missing.append("DISCORD_BOT_TOKEN")
    if missing:
        raise SystemExit(
            "missing in .env: " + ", ".join(missing)
            + "\ncopy .env.example to .env and fill it — see README, 'Host it yourself'."
        )


def start_heartbeat(game: Game):
    # Hosts like Render only keep a free web service awake while something
    # answers HTTP on $PORT. The same server is now the spectator view:
    # `/` is the live constellation, `/state.json` feeds it. No message
    # content ever leaves state_snapshot().
    port = os.environ.get("PORT")
    if not port:
        return
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    import constellation

    page = constellation.render_page().encode()

    class Pulse(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/state.json"):
                try:
                    body = json.dumps(game.state_snapshot()).encode()
                except Exception as e:
                    print(f"!! snapshot failed: {e}")
                    body = b"{}"
                ctype = "application/json"
            else:
                body, ctype = page, "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("0.0.0.0", int(port)), Pulse)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"heartbeat + constellation on :{port}")

    # Free-tier hosts sleep after ~15 min without inbound traffic on the
    # public URL, and player messages arrive over the SDK, not HTTP — so
    # ping our own public URL to stay awake.
    public_url = os.environ.get("RENDER_EXTERNAL_URL")
    if public_url:
        import urllib.request
        ping_url = public_url.rstrip("/") + "/state.json"

        def pulse():
            while True:
                time.sleep(300)
                try:
                    urllib.request.urlopen(ping_url, timeout=30).read()
                except Exception:
                    pass

        threading.Thread(target=pulse, daemon=True).start()
        print(f"self-ping every 5 min -> {public_url}")


def main():
    personas.load_env()
    preflight()
    client = CommClient()
    game = Game(client)
    start_heartbeat(game)
    connect(client, game)

    @client.on_message
    def handle(message):
        game.on_message(message)

    @client.on_interaction
    def tapped(interaction):
        game.on_interaction(interaction)

    game.start_ticker()
    print("\nSAFE OR SURE — listening. say hi to any room to start. ctrl-c to stop\n")
    try:
        client.listen()
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # A dead listener with a live heartbeat is a zombie: the host sees a
        # healthy service while the game is deaf. Die loudly; Render restarts.
        print(f"!! listener died: {e}")
        raise SystemExit(1)
    print("!! listener returned — exiting so the host restarts us")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
