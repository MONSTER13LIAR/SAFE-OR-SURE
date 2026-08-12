"""Offline engine smoke test — many players at once, no keys, no network.

Drives the real handler with fake channels and a stubbed persona engine.
Its one job is the promise the hosted game makes: several strangers can
play the same instance simultaneously and never touch each other's run.

Run:  .venv/bin/python smoke.py
"""

import os
import time

os.environ.setdefault("RUN_PACE", "demo")
os.environ.setdefault("DISCORD_INVITE_URL", "https://discord.gg/test")
os.environ.setdefault("TELEGRAM_BOT_URL", "https://t.me/test_bot")
os.environ.pop("PLAYER_EMAIL", None)
os.environ.pop("PLAYER_DISCORD_ID", None)

import personas  # noqa: E402  (importing it loads the real .env)

for k in ("PLAYER_EMAIL", "PLAYER_DISCORD_ID", "SOLO_TEST"):
    os.environ.pop(k, None)

# ---------------------------------------------------------------- stubs
SENT = []          # (conversation, text)
INITIATED = []     # (connection, recipient, text)


def fake_turn(persona, history, beat, own_facts=(), leak_facts=(),
              allowed_facts=(), new_fact=None, notes=""):
    return personas.PersonaTurn(
        message=f"[{persona}:{beat}]",
        facts_used=[f.id for f in leak_facts],
    )


personas.persona_turn = fake_turn

import director as DIR  # noqa: E402
import game as G  # noqa: E402

G.COLD_OPEN_DELAY = (0.02, 0.03)
G.DOOR_DROP_DELAY = (0.02, 0.03)
G.BLOCK_POLL_SECONDS = (0.05,)   # the fake gateway reports nothing queued


class FakeClient:
    def send_message(self, conversation, text=None, blocks=None):
        SENT.append((conversation, text if text is not None else blocks))
        return {"id": f"m{len(SENT)}"}

    def initiate(self, connection, recipient, text):
        INITIATED.append((connection, recipient, text))
        return {"id": f"i{len(INITIATED)}"}

    def list_messages(self, conversation):
        return []


class Msg:
    def __init__(self, conn, conv, text, sender):
        self.connection_id = conn
        self.conversation_id = conv
        self.text = text
        self.sender = sender

    def reply(self, text=None, blocks=None):
        SENT.append((self.conversation_id, text if text is not None else blocks))
        return {"id": f"r{len(SENT)}"}


class Tap:
    def __init__(self, conn, conv, value):
        self.connection_id = conn
        self.conversation_id = conv
        self.value = value


CONN = {"telegram": "c-tg", "discord": "c-dc", "email": "c-em"}

hub = G.Game(FakeClient())
hub.conn_to_room = {v: k for k, v in CONN.items()}
hub.game_email = "game@agents.trycaspianai.com"
hub.telegram_url = "https://t.me/test_bot"

checks = []


def check(label, ok):
    checks.append((label, bool(ok)))
    print(("  ok   " if ok else "  FAIL ") + label)


def say(room, conv, text, sender):
    hub.on_message(Msg(CONN[room], conv, text, sender))
    time.sleep(0.15)


def tap(room, conv, value):
    hub.on_interaction(Tap(CONN[room], conv, value))
    time.sleep(0.15)


def sent_to(conv):
    return [t for c, t in SENT if c == conv]


# ---------------------------------------------------------------- 1. two players
print("\n1. two strangers say hi to Maria")
say("telegram", "tg-A", "hey", {"name": "Ravi", "id": "u-A"})
say("telegram", "tg-B", "hello", {"name": "Sana", "id": "u-B"})
runs = hub.live()
check("two separate runs exist", len(runs) == 2)
A = hub.by_conv["tg-A"]
B = hub.by_conv["tg-B"]
check("the two runs are different objects", A is not B)
check("each run got a greeting", sent_to("tg-A") and sent_to("tg-B"))

# ---------------------------------------------------------------- 2. isolation
print("\n2. what one player plants stays in that player's run")
tap("telegram", "tg-A", "plant:beagle")
check("A planted the beagle", A.mind.get("beagle").origin == "telegram")
check("B's beagle is untouched", B.mind.get("beagle").origin is None)
check("B's mind has none of A's facts",
      not [f for f in B.mind.planted() if f.id == "beagle"])
tap("telegram", "tg-B", "plant:mangoes")
check("A never sees B's mangoes", A.mind.get("mangoes").origin is None)

# ---------------------------------------------------------------- 3. email join
print("\n3. the email a player hands over joins their own run")
A.director.email_asks = 1          # Maria has asked
say("telegram", "tg-A", "its ravi@example.com", {"name": "Ravi", "id": "u-A"})
check("A's address was learned", A.player_email == "ravi@example.com")
check("Priya cold-opened to A only",
      [i for i in INITIATED if i[1] == "ravi@example.com"])
say("email", "em-A", "who is this", {"name": "Ravi", "address": "ravi@example.com"})
check("A's email lands in A's run", hub.by_conv["em-A"] is A)
check("no new run was created", len(hub.live()) == 2)

print("   a stranger's email starts its own run, not somebody else's")
say("email", "em-X", "hello?", {"name": "Nobody", "address": "nobody@example.com"})
check("stranger got their own run", hub.by_conv["em-X"] not in (A, B))
check("three runs live now", len(hub.live()) == 3)

# ---------------------------------------------------------------- 4. discord join
print("\n4. the discord name a player hands over joins their own run")
B.director.doors_dropped.add("discord")
B.director.handle_asks = 1
B.director.handle_answer_window = 2      # the ask just went out
say("telegram", "tg-B", "im sana_k over there", {"name": "Sana", "id": "u-B"})
check("B's handle was learned", "sana_k" in (B.expect.get("discord") or []))

print("   a sentence later in the run is not a discord name")
B.expect.pop("discord", None)
B.director.handle_answer_window = 0
say("telegram", "tg-B", "do u know anything about the printer?",
    {"name": "Sana", "id": "u-B"})
check("no handle was invented from ordinary chat", not B.expect.get("discord"))
B.expect["discord"] = ["sana_k"]         # put it back for the rest of the run
say("discord", "dc-B", "hi", {"name": "sana_k", "id": "u-B-dc"})
check("B's discord lands in B's run", hub.by_conv["dc-B"] is B)
check("still three runs", len(hub.live()) == 3)

print("   an unrecognised discord stranger gets their own run")
say("discord", "dc-Y", "yo", {"name": "someone_else", "id": "u-Y"})
check("stranger did not land in B's run", hub.by_conv["dc-Y"] is not B)
check("four runs live", len(hub.live()) == 4)

# ---------------------------------------------------------------- 5. stale taps
print("\n5. a button from another run's thread does nothing")
before = A.mind.get("rice").origin
tap("telegram", "tg-B", "plant:rice")   # B's thread, B's run
check("A's rice is untouched", A.mind.get("rice").origin == before)
hub.on_interaction(Tap(CONN["telegram"], "tg-ghost", "plant:tap"))
check("a tap from an unknown thread is ignored",
      A.mind.get("tap").origin is None and B.mind.get("tap").origin is None)

# ---------------------------------------------------------------- 6. scoring
print("\n6. flags score inside one run only")
A.ledger.opened["discord"] = True
turn = A.ledger.record_turn("discord", "that beagle again", ["beagle"])
result = A.ledger.flag(turn.id)
check("A's cross-room reuse is a link", result["verdict"] == "link")
check("A's flag count dropped", A.ledger.flags_left == 5)
check("B's flags are untouched", B.ledger.flags_left == 6)

# ---------------------------------------------------------------- 7. reset
print("\n7. one player restarting leaves everyone else alone")
b_epoch = B.epoch
say("telegram", "tg-A", "reset", {"name": "Ravi", "id": "u-A"})
check("A's run is fresh", A.mind.get("beagle").origin is None)
check("A keeps their thread", A.conversations.get("telegram") == "tg-A")
check("A keeps the address they gave", A.player_email == "ravi@example.com")
check("B's run untouched", B.epoch == b_epoch and B.mind.get("mangoes").origin == "telegram")

# ---------------------------------------------------------------- 8. capacity
print("\n8. the game fills up politely instead of breaking")
G.MAX_SESSIONS = len(hub.live())
SENT.clear()
say("telegram", "tg-Z", "hi?", {"name": "Late", "id": "u-Z"})
check("no run was created past the cap", "tg-Z" not in hub.by_conv)
check("they were told, kindly", any(t == G.deck.BUSY for t in sent_to("tg-Z")))
G.MAX_SESSIONS = 12
print("   ...and a returning player still gets through a full house")
G.MAX_SESSIONS = len(hub.live())
say("telegram", "tg-B", "still here", {"name": "Sana", "id": "u-B"})
check("known player routed while full", hub.by_conv["tg-B"] is B)
G.MAX_SESSIONS = 12

# ---------------------------------------------------------------- 9. sweep
print("\n9. abandoned runs free their seat")
stranger = hub.by_conv["em-X"]
stranger.last_seen = 0
stranger.director.last_player_action = 0
hub._sweep()
check("the abandoned run is gone", stranger.dead and stranger not in hub.sessions)
check("its threads are unrouted", "em-X" not in hub.by_conv)
check("live runs still playable", A in hub.live() and B in hub.live())

# ------------------------------------------------- 10. endings always land
print("\n10. an ending always reaches the player, inbox or not")
# Two rooms open, no inbox, then they block Deke. Winning is now
# impossible, so the run ends — and the ending used to be posted to the
# email room they never opened, i.e. nowhere at all.
say("telegram", "tg-C", "hi", {"name": "Cass", "id": "u-C"})
C = hub.by_conv["tg-C"]
C.expect["discord"] = ["cass"]      # they answered the "whats your discord" ask
say("discord", "dc-C", "hi", {"name": "cass", "id": "u-C-dc"})
check("both rooms belong to the same person", hub.by_conv["dc-C"] is C)
check("the inbox was never opened", not C.ledger.opened["email"])
SENT.clear()
C._room_sealed("discord")
time.sleep(0.3)
check("the run ended", C.ledger.ending == "CORNERED")
reached = [t for c, t in SENT if c == "tg-C"]
check("the ending was said somewhere they can hear it", bool(reached))
check("no inbox means the honest copy",
      any(isinstance(t, str) and "never opened" in t for t in reached))
check("the case file landed too, with its button",
      any(not isinstance(t, str) for t in reached))

print("   [run it back] still works after the run has been swept")
C.last_seen = 0
C.director.last_player_action = 0
C.ended_at = 0
hub._sweep()
check("the run was swept", C.dead)
SENT.clear()
tap("telegram", "tg-C", "reset")
check("the tap opened a fresh run", hub.by_conv.get("tg-C") not in (None, C))
check("and answered instead of going silent",
      any(t == G.deck.RESET_OK for t in sent_to("tg-C")))

# ------------------------------------------- 11. a game for two, in private
print("\n11. a bystander in a shared thread is sent to DMs, not into the run")
D = hub.by_conv["dc-Y"]                      # the discord stranger from step 4
flags_before = D.ledger.flags_left
SENT.clear()
say("discord", "dc-Y", "wait what is this", {"name": "loud_bystander", "id": "u-Q"})
check("the bystander was answered once",
      any(t == G.deck.NOT_IN_PUBLIC["deke"] for t in sent_to("dc-Y")))
check("their words never entered the run",
      not any(h["text"] == "wait what is this" for h in D.history["discord"]))
SENT.clear()
say("discord", "dc-Y", "hello??", {"name": "loud_bystander", "id": "u-Q"})
check("and not answered again", not sent_to("dc-Y"))
hub.on_interaction(Tap(CONN["discord"], "dc-Y", "flag:t0"))
check("their taps can't spend the player's flags",
      D.ledger.flags_left == flags_before)
check("the room still belongs to whoever spoke in it first",
      D.keys["discord"] == "u-y")   # the sender id, not the display name

# ---------------------------------------------------------------- 12. spectator
print("\n10. the page sees shapes, never words")
snap = hub.state_snapshot()
check("one entry per live run", len(snap["runs"]) == len(hub.live()))
check("runs carry no message text",
      "beagle" not in str(snap) and "hey" not in str(snap))
check("doors are offered", set(snap["doors"]) == {"telegram", "discord", "email"})

# ------------------------------------------- 13. a first-timer's first minutes
# Playtest 2026-08-12: a stranger said hi, planted one fact, and was then
# shown exactly one button — the flag — on a message that could not
# possibly be a link, because only one room was open. They burned a flag
# and quit. Everything here is that run, made impossible.
print("\n13. the first two minutes of a stranger's first run")
SENT.clear()
say("telegram", "tg-N", "hi", {"name": "New", "id": "u-N"})
N = hub.by_conv["tg-N"]
first = sent_to("tg-N")
check("the rules arrive before anyone says hello",
      first and first[0] == G.deck.OPENING_CARD)
check("and only once", sum(1 for t in first if t == G.deck.OPENING_CARD) == 1)
check("no flag button while one room is open",
      not any("flag:" in str(t) for t in first))
check("but something to do", any("plant:" in str(t) for t in first))

say("telegram", "tg-N", "ok", {"name": "New", "id": "u-N"})
check("the second door is handed over immediately",
      "discord" in N.director.doors_dropped)

N.expect["discord"] = ["newbie"]
say("discord", "dc-N", "hi", {"name": "newbie", "id": "u-N-dc"})
SENT.clear()
say("telegram", "tg-N", "hello again", {"name": "New", "id": "u-N"})
check("the flag button appears once a flag could be right",
      any("flag:" in str(t) for t in sent_to("tg-N")))

print("   the first wrong flag is free, and says why")
t1 = N.ledger.record_turn("telegram", "just talk", [])
check("free verdict", N.ledger.flag(t1.id)["verdict"] == "free")
check("it cost nothing", N.ledger.flags_left == 6 and N.ledger.wrong == 0)
t2 = N.ledger.record_turn("telegram", "still just talk", [])
check("the second one costs", N.ledger.flag(t2.id)["verdict"] == "noise")
check("and counts against them", N.ledger.flags_left == 5 and N.ledger.wrong == 1)

print("   a player who never answers the email ask still gets the inbox")
N.director.doors_dropped.add("discord")
N.director.email_asks = 0
N.director.maybe_drop_doors("telegram")
check("the address is not handed out while it can still ask",
      "email" not in N.director.doors_dropped)
N.director.email_asks = len(DIR.EMAIL_ASK_AT)
SENT.clear()
N.director.maybe_drop_doors("telegram")
time.sleep(0.2)
check("once the asks are spent, the door is handed over",
      any(hub.game_email in str(t) for t in sent_to("tg-N")))

# ------------------------------------------- 14. the inbox has no buttons
# Reported live 2026-08-12: taps do nothing in email, because mail clients
# strip interactive blocks. Email is act 3 and the room that can never be
# sealed — a player must never be reduced to watching it.
print("\n14. in email, words do what buttons do everywhere else")
hint = G.deck.email_actions([{"value": "flag:t1"}, {"value": "plant:mangoes"}])
check("the hint spells out both moves", "`flag`" in hint and "`mangoes`" in hint)

say("email", "em-M", "hello", {"name": "Mail", "address": "mail@example.com"})
M = hub.by_conv["em-M"]
SENT.clear()
say("email", "em-M", "beagle", {"name": "Mail", "address": "mail@example.com"})
check("a bare fact name plants it", M.mind.get("beagle").origin == "email")
check("and she reacts to being told", any("react_plant" in str(t) for t in sent_to("em-M")))

M.ledger.opened["telegram"] = True      # two rooms up: buttons exist now
SENT.clear()
say("email", "em-M", "ok what else", {"name": "Mail", "address": "mail@example.com"})
check("email messages carry the words for the taps",
      any("no buttons in email" in str(t) for t in sent_to("em-M")))

# ---------------------------------------------------------------- report
bad = [label for label, ok in checks if not ok]
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
if bad:
    for label in bad:
        print(f"  FAILED: {label}")
    raise SystemExit(1)
print("many players, one instance, nothing crossed.")
