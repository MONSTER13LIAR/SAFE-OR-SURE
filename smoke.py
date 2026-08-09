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

import game as G  # noqa: E402

G.COLD_OPEN_DELAY = (0.02, 0.03)
G.DOOR_DROP_DELAY = (0.02, 0.03)
G.BLOCK_POLL_SECONDS = ()


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
say("telegram", "tg-B", "im sana_k over there", {"name": "Sana", "id": "u-B"})
check("B's handle was learned", "sana_k" in (B.expect.get("discord") or []))
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

# ---------------------------------------------------------------- 10. spectator
print("\n10. the page sees shapes, never words")
snap = hub.state_snapshot()
check("one entry per live run", len(snap["runs"]) == len(hub.live()))
check("runs carry no message text",
      "beagle" not in str(snap) and "hey" not in str(snap))
check("doors are offered", set(snap["doors"]) == {"telegram", "discord", "email"})

# ---------------------------------------------------------------- report
bad = [label for label, ok in checks if not ok]
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
if bad:
    for label in bad:
        print(f"  FAILED: {label}")
    raise SystemExit(1)
print("many players, one instance, nothing crossed.")
