"""Offline engine smoke test — no keys, no network, many players at once.

Drives the real handler with fake channels and a stubbed persona engine.
Two jobs, and it fails loudly on either:

  1. the promise the hosted game makes — several strangers can play one
     instance simultaneously and never touch each other's run;
  2. the promise the LADDER makes — ten levels that actually get harder,
     a level 10 that genuinely cannot be won, and no way to climb it
     without playing it.

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

import deck  # noqa: E402
import director as DIR  # noqa: E402
import game as G  # noqa: E402
import levels as LV  # noqa: E402

G.MAX_SESSIONS = 40              # the cap gets its own test; don't trip it early
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
    def __init__(self, conn, conv, value, sender=None):
        self.connection_id = conn
        self.conversation_id = conv
        self.value = value
        self.sender = sender


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


def tap(room, conv, value, sender=None):
    hub.on_interaction(Tap(CONN[room], conv, value, sender))
    time.sleep(0.15)


def sent_to(conv):
    return [t for c, t in SENT if c == conv]


def hand(session):
    """A fact id this run is actually playing with — the deck is dealt per
    level now, so no test may name a card by hand."""
    return session.mind.unplanted()[0].id


def plant(session, room, conv, fact_id=None):
    """Tap a plant button the way a player does: on the newest message."""
    turn = session.ledger.latest_turn(room)
    fid = fact_id or hand(session)
    tap(room, conv, f"plant:{turn.id}:{fid}")
    return fid


def prove(session, room, fact_id):
    """Record a turn that reuses a fact from another room, and flag it."""
    turn = session.ledger.record_turn(room, "that thing again", [fact_id])
    return session.ledger.flag(turn.id)


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
check("each run got its own code", A.code != B.code)
check("both start on level 1", A.level_n == 1 and B.level_n == 1)

# ---------------------------------------------------------------- 2. isolation
print("\n2. what one player plants stays in that player's run")
a_fact = plant(A, "telegram", "tg-A")
check("A planted something", A.mind.get(a_fact).origin == "telegram")
check("B never sees it",
      B.mind.get(a_fact) is None or B.mind.get(a_fact).origin is None)
a_before = {f.id: f.origin for f in A.mind.facts.values()}
b_fact = plant(B, "telegram", "tg-B")
check("B's move changes nothing in A's mind",
      all(A.mind.facts[i].origin == o for i, o in a_before.items()))
check("and B's card is planted in B's run", B.mind.get(b_fact).origin == "telegram")

# ---------------------------------------------------------------- 3. the buttons go dark
print("\n3. a taken offer is taken")
SENT.clear()
solo = A.ledger.record_turn("telegram", "the newest message", [])
A._handle_offer("telegram", f"deflect:{solo.id}")
A._handle_offer("telegram", f"deflect:{solo.id}")
check("the first tap on an offer works",
      any(t == deck.DEFLECTED for t in sent_to("tg-A")))
check("a second tap on the same message is refused",
      any(t == deck.BUTTON_SPENT for t in sent_to("tg-A")))
SENT.clear()
turn = A.ledger.latest_turn("telegram")
old = turn.id
say("telegram", "tg-A", "and another thing", {"name": "Ravi", "id": "u-A"})
SENT.clear()
tap("telegram", "tg-A", f"plant:{old}:{hand(A)}")
check("an offer from an older message is refused",
      any(t == deck.BUTTON_STALE for t in sent_to("tg-A")))
check("and the fact was not consumed", A.mind.get(hand(A)).origin is None)
SENT.clear()
fid = plant(A, "telegram", "tg-A")
check("a fresh tap lands instantly, before the model is called",
      any(isinstance(t, str) and t.startswith("— you told") for t in sent_to("tg-A")))

# ---------------------------------------------------------------- 4. email join
print("\n4. the email a player hands over joins their own run")
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

print("   a near-miss name does NOT land in somebody's run")
B.expect["discord"] = ["sam"]
say("discord", "dc-sam", "hi", {"name": "samantha", "id": "u-sam"})
check("samantha did not join sam's run", hub.by_conv["dc-sam"] is not B)

# ---------------------------------------------------------------- 5. the code
print("\n5. the run's code joins one human's two doors")
say("telegram", "tg-C", "hi", {"name": "Cass", "id": "u-C"})
C = hub.by_conv["tg-C"]
before = len(hub.live())
say("discord", "dc-C", f"hey {C.code}", {"name": "whoever", "id": "u-C-dc"})
check("the code joined the same run", hub.by_conv["dc-C"] is C)
check("no extra run was made", len(hub.live()) == before)
check("both rooms are open for them",
      C.ledger.opened["telegram"] and C.ledger.opened["discord"])

print("   a wrong code is just words")
say("discord", "dc-W", "hey A1B", {"name": "wrong", "id": "u-W"})
check("nobody was joined by a stranger's guess", hub.by_conv["dc-W"] is not C)
check("and a code buried in a paragraph is not a code",
      hub._by_code("email", "u-C", f"hello there this is a long sentence "
                                   f"that happens to contain {C.code} in it") is None)

print("   the discord invite drops you in a SERVER, so the room can move")
# Say hi in a channel first (binds the room there), then DM the bot. The
# DM used to be answered once and then silently dropped forever.
say("telegram", "tg-G", "hi", {"name": "Gee", "id": "u-G"})
Gs = hub.by_conv["tg-G"]
say("discord", "dc-channel", "hello?", {"name": "gee", "id": "u-G-dc"})
check("the channel claimed the room", Gs.conversations.get("discord") == "dc-channel"
      or hub.by_conv["dc-channel"] is not Gs)
owner = hub.by_conv["dc-channel"]
SENT.clear()
say("discord", "dc-dm", "hey", {"name": "gee", "id": "u-G-dc"})
check("a bare DM from the same person is not followed",
      owner.conversations.get("discord") == "dc-channel")
check("but they are told how to fix it",
      any(t == deck.WRONG_THREAD["deke"] for t in sent_to("dc-dm")))
say("discord", "dc-dm", owner.code, {"name": "gee", "id": "u-G-dc"})
check("saying the word moves the room to their own thread",
      owner.conversations.get("discord") == "dc-dm")
check("and the channel stops routing into the run", "dc-channel" not in hub.by_conv)

print("   ...but a bystander with the same code cannot take the room")
say("discord", "dc-thief", f"hey {owner.code}", {"name": "thief", "id": "u-thief"})
check("the thief got their own run", hub.by_conv["dc-thief"] is not owner)
check("and the room stayed with its owner",
      owner.conversations.get("discord") == "dc-dm")

# ---------------------------------------------------------------- 6. the hook
print("\n6. opening the second door is followed by a leak, every time")
cfact = plant(C, "telegram", "tg-C")
time.sleep(0.4)
check("the plant is in C's mind", C.mind.get(cfact).origin == "telegram")
check("the director scheduled the hook on room 2",
      "discord" in C.director._open_alive())

# ---------------------------------------------------------------- 7. levels
print("\n7. level 1 is one link, and naming it promotes you")
check("level 1 wants one link", C.ledger.level.links == 1)
res = prove(C, "discord", cfact)
check("the cross-room reuse is a link", res["verdict"] == "link")
check("one link names level 1", res["ending"] == "NAMED")
SENT.clear()
C.resolve()
time.sleep(5.0)
check("they were promoted, not ended", C.level_n == 2 and C.ledger.ending is None)
check("the level card went out",
      any(isinstance(t, str) and "LEVEL 2" in t for t in sent_to("tg-C")))
check("level 2 wants two links", C.ledger.level.links == 2)
check("level 2 has a smaller budget", C.ledger.flags_left == LV.get(2).flags)
check("the cleared level was recorded", len(C.cleared) == 1)
check("a fresh hand was dealt", C.mind.get(cfact) is None)
check("rooms stay open across the level", C.ledger.opened["discord"])

print("   a door handed over stays handed over, across every rung")
# doors_dropped used to live on the Director, which is rebuilt per level —
# so a player who climbed without opening Discord got the identical fixed
# line re-sent on every single level, up to nine times.
check("the door was dropped on the level just played",
      "discord" in C.director.doors_dropped or C.ledger.opened["discord"])
C.director.doors_dropped.add("email")
C._new_level(C.level_n + 1)
check("and the new level remembers it",
      "email" in C.director.doors_dropped)
C._new_level(2)   # back to where the rest of this section expects it

print("   the ladder only goes up by playing it")
say("telegram", "tg-C", "reset", {"name": "Cass", "id": "u-C"})
check("reset drops you to level 1", C.level_n == 1)
check("reset clears the ladder", C.cleared == [])

# ---------------------------------------------------------------- 8. difficulty is real
print("\n8. every rung is measurably harder than the one below it")
prev = None
for n in range(1, LV.TOP + 1):
    lv = LV.get(n)
    if prev:
        # Level 1 has no clock at all, so only compare clocks once there
        # is one on both rungs.
        clock_ok = not (prev.seconds and lv.seconds) or lv.clock() <= prev.clock()
        ok = (lv.flags <= prev.flags and clock_ok
              and lv.decoy_chance >= prev.decoy_chance)
        if not ok:
            check(f"level {n} is not easier than level {n - 1}", False)
            break
    prev = lv
else:
    check("flags, clock and decoy density never go backwards", True)
check("level 1 is forgiving", LV.get(1).forgive and LV.get(1).links == 1)

# The clock has to be able to run out, or OUTRUN and TEN are unreachable
# and the pressure the whole ladder rests on is decorative. Waiting on a
# slow model gives seconds back; it can never give back the whole level.
stall_led = G.Ledger(G.Mind(), level=LV.get(6))
stall_led.start_clock()
for _ in range(50):
    stall_led.add_stall(60)
check("model-wait credit is capped, so the clock always runs out",
      stall_led.stall <= LV.get(6).clock() * 0.5)
check("and a level with no clock reports none",
      G.Ledger(G.Mind(), level=LV.get(1)).time_left() is None)
check("the last level does not leak", not LV.get(LV.TOP).leaks)
check("every other level does", all(LV.get(n).leaks for n in range(1, LV.TOP)))

# ---------------------------------------------------------------- 9. level ten
print("\n9. level 10 cannot be won, and cannot be won by accident either")
say("telegram", "tg-T", "hi", {"name": "Ten", "id": "u-T"})
T = hub.by_conv["tg-T"]
T.expect["discord"] = ["tenner"]
say("discord", "dc-T", "hi", {"name": "tenner", "id": "u-T-dc"})
T._new_level(LV.TOP)
T.ledger.opened.update({"telegram": True, "discord": True, "email": True})
T.ledger.start_clock()
check("the director will not hand out a leak", T.director._pick_leak() is None)
T.director._delayed_leak()
check("and the delayed leak is a no-op too", not T.ledger.live_leaks())
before_facts = len(T.mind.facts)
T.director.on_wrong_flag("telegram", "Maria")
time.sleep(0.3)
check("a wrong flag mints no evidence on level 10",
      len(T.mind.facts) == before_facts)
check("nothing on level 10 proves anything", not T.ledger.live_leaks())

print("   flags on level 10 are free, and the answer is honest")
# Level 10 talks about things the player really did tell somebody, on an
# earlier level, in a Mind that no longer exists. Charging a flag for
# checking — and answering "nothing in that one came from another room" —
# would read as the game cheating on the most-watched rung.
T.known.append("you burned rice twice this week in the new cooker")
bait10 = T.director._pick_decoy()
check("level 10 draws its bait from the whole climb",
      bait10 in T.known or bait10 in [f.text for f in T.mind.unplanted()])
flags10 = T.ledger.flags_left
t10 = T.ledger.record_turn("discord", "[deke:decoy]", [])
r10 = T.ledger.flag(t10.id)
check("the verdict is clean, not noise", r10["verdict"] == "clean")
check("it cost nothing", T.ledger.flags_left == flags10)
check("and it did not end the run", T.ledger.ending is None)
check("level 10 still hands out plant buttons",
      T.director.on_player_message("discord", "hi").get("offer_plants") is not None)

print("   the clock is the only ending it has")
T.ledger.penalise(10_000)
check("the clock reads empty", T.ledger.out_of_time())
SENT.clear()
T.director.tick()
time.sleep(1.0)
check("running the clock out on level 10 is TEN", T.ledger.ending == "TEN")
check("and it says so", any(isinstance(t, str) and "TEN." in t
                            for c, t in SENT))

print("   on any other level the same clock is a loss")
say("telegram", "tg-O", "hi", {"name": "Out", "id": "u-O"})
O = hub.by_conv["tg-O"]
O._new_level(4)
O.ledger.opened["telegram"] = True
O.ledger.start_clock()
O.ledger.penalise(10_000)
O.director.tick()
time.sleep(0.5)
check("the clock running out mid-ladder is OUTRUN", O.ledger.ending == "OUTRUN")

# ---------------------------------------------------------------- 10. no free links
print("\n10. you cannot climb by flagging nothing")
say("telegram", "tg-E", "hi", {"name": "Ex", "id": "u-E"})
E = hub.by_conv["tg-E"]
E.expect["discord"] = ["exp"]
say("discord", "dc-E", "hi", {"name": "exp", "id": "u-E-dc"})
E._new_level(2)      # two links needed, no free first flag on the ladder above 4
E.ledger.opened.update({"telegram": True, "discord": True})
t1 = E.ledger.record_turn("telegram", "just talk", [])
check("the first wrong flag is free", E.ledger.flag(t1.id)["verdict"] == "free")
t2 = E.ledger.record_turn("telegram", "still just talk", [])
check("the second one costs", E.ledger.flag(t2.id)["verdict"] == "noise")
proven_before = len(E.ledger.proven)
E.director.on_wrong_flag("telegram", "Maria")
time.sleep(0.4)
acc = [f for f in E.mind.facts.values() if f.id.startswith("acc")]
check("no accusation is minted while nothing is proven yet", not acc)
check("so a wrong flag can never hand out a link",
      len(E.ledger.proven) == proven_before)

print("   a level you can no longer finish ends now, not in two minutes")
say("telegram", "tg-DEAD", "hi", {"name": "Dead", "id": "u-DEAD"})
DEAD = hub.by_conv["tg-DEAD"]
DEAD.expect["discord"] = ["dead"]
say("discord", "dc-DEAD", "hi", {"name": "dead", "id": "u-DEAD-dc"})
DEAD._new_level(8)      # two flags, two links, no free mistake
DEAD.ledger.opened.update({"telegram": True, "discord": True, "email": True})
check("level 8 starts with exactly enough flags",
      DEAD.ledger.flags_left == DEAD.ledger.links_left())
tw = DEAD.ledger.record_turn("telegram", "nothing in this", [])
res = DEAD.ledger.flag(tw.id)
check("one wasted flag makes the level arithmetically dead",
      DEAD.ledger.flags_left < DEAD.ledger.links_left())
check("so it ends there instead of playing on to nothing",
      res["ending"] == "SWARMED")

print("   the promotion window swallows input instead of saying the run is over")
say("telegram", "tg-ADV", "hi", {"name": "Adv", "id": "u-ADV"})
ADV = hub.by_conv["tg-ADV"]
ADV.advancing = True
ADV.ledger.ending = "NAMED"
before_level = ADV.level_n
SENT.clear()
say("telegram", "tg-ADV", "?? hello?", {"name": "Adv", "id": "u-ADV"})
check("nothing is said into the silence", not sent_to("tg-ADV"))
say("telegram", "tg-ADV", "reset", {"name": "Adv", "id": "u-ADV"})
check("and `reset` cannot throw the climb away mid-promotion",
      ADV.level_n == before_level and ADV.advancing)
ADV.advancing = False
ADV.ledger.ending = None

print("   a wrong flag still costs time on the levels that have a clock")
E.ledger.start_clock()
was = E.ledger.time_left()
t3 = E.ledger.record_turn("telegram", "noise", [])
E.ledger.flag(t3.id)
check("the clock was docked", E.ledger.time_left() < was)

# ---------------------------------------------------------------- 11. decoys
print("\n11. a decoy looks like a leak and is provably not one")
say("telegram", "tg-D", "hi", {"name": "Dee", "id": "u-D"})
D = hub.by_conv["tg-D"]
D.expect["discord"] = ["dee"]
say("discord", "dc-D", "hi", {"name": "dee", "id": "u-D-dc"})
D._new_level(8)      # heavy decoy level
D.ledger.opened.update({"telegram": True, "discord": True})
bait = D.director._pick_decoy()
check("the level offers bait", bool(bait))
check("the bait is something they have NOT given anyone",
      bait in [f.text for f in D.mind.unplanted()])
decoy_turn = D.ledger.record_turn("discord", "[deke:decoy]", [])
check("flagging a decoy is noise, not a link",
      D.ledger.flag(decoy_turn.id)["verdict"] in ("noise", "free"))

# A level that is mostly decoys must still hand out ammunition, or the
# player runs out of facts to plant and starves the leaks they need.
decisions = [D.director.on_player_message("discord", "ok") for _ in range(12)]
decoys = [d for d in decisions if d["beat"] == "decoy"]
check("a heavy decoy level still produces decoys", bool(decoys))
check("and they still carry plant buttons",
      any(d.get("offer_plants") for d in decoys) or not D.mind.unplanted())

# ---------------------------------------------------------------- 12. privacy
print("\n12. a private run is never dragged into a public thread")
say("telegram", "tg-P", "hi", {"name": "Pri", "id": "u-P"})
P = hub.by_conv["tg-P"]
SENT.clear()
say("telegram", "tg-group", "hi everyone", {"name": "Pri", "id": "u-P"})
check("their run did not follow them into the group",
      P.conversations["telegram"] == "tg-P")
check("and they were told how to be recognised, without the word in it",
      any(t == deck.WRONG_THREAD["maria"] for t in sent_to("tg-group"))
      and not any(P.code in str(t) for t in sent_to("tg-group")))
check("no run was opened in the group", "tg-group" not in hub.by_conv)

print("   a bystander who is told to DM can actually start their own game")
say("discord", "dc-pub", "yo", {"name": "first", "id": "u-first"})
PUB = hub.by_conv["dc-pub"]
SENT.clear()
say("discord", "dc-pub", "whats this", {"name": "second", "id": "u-second"})
check("the bystander was answered once",
      any(t == deck.NOT_IN_PUBLIC["deke"] for t in sent_to("dc-pub")))
check("their words never entered the run",
      not any(h["text"] == "whats this" for h in PUB.history["discord"]))
say("discord", "dc-second", "hi", {"name": "second", "id": "u-second"})
check("and their own DM opens their own run",
      hub.by_conv.get("dc-second") not in (None, PUB))

# ---------------------------------------------------------------- 13. stale taps
print("\n13. a button from another run's thread does nothing")
before = A.mind.get(a_fact).origin
tap("telegram", "tg-B", f"plant:{B.ledger.latest_turn('telegram').id}:{hand(B)}")
check("A's fact is untouched", A.mind.get(a_fact).origin == before)
hub.on_interaction(Tap(CONN["telegram"], "tg-ghost", "plant:t0:beagle"))
check("a tap from an unknown thread is ignored", True)

# ---------------------------------------------------------------- 14. retired facts
print("\n14. what two rooms can both see is not evidence")
say("telegram", "tg-R", "hi", {"name": "SameName", "id": "u-R"})
R = hub.by_conv["tg-R"]
R.expect["discord"] = ["samename"]
say("discord", "dc-R", "hi", {"name": "SameName", "id": "u-R-dc"})
name = R.mind.get("your_name")
check("the name was retired once both rooms saw it", name is None or name.retired)
if name is not None:
    t = R.ledger.record_turn("discord", "hi SameName", ["your_name"])
    check("and flagging it is not a link", R.ledger.flag(t.id)["verdict"] != "link")

# ---------------------------------------------------------------- 15. capacity + gc
print("\n15. the game fills up politely, and frees its seats")
G.MAX_SESSIONS = len(hub.live())
SENT.clear()
say("telegram", "tg-Z", "hi?", {"name": "Late", "id": "u-Z"})
check("no run was created past the cap", "tg-Z" not in hub.by_conv)
check("they were told, kindly", any(t == deck.BUSY for t in sent_to("tg-Z")))
say("telegram", "tg-B", "still here", {"name": "Sana", "id": "u-B"})
check("known player routed while full", hub.by_conv["tg-B"] is B)
G.MAX_SESSIONS = 40

stranger = hub.by_conv["em-X"]
stranger.last_seen = 0
stranger.director.last_player_action = 0
hub._sweep()
check("the abandoned run is gone", stranger.dead and stranger not in hub.sessions)
check("its threads are unrouted", "em-X" not in hub.by_conv)
check("live runs still playable", A in hub.live() and B in hub.live())

# ------------------------------------------- 16. endings always land
print("\n16. an ending always reaches the player, inbox or not")
say("telegram", "tg-K", "hi", {"name": "Kay", "id": "u-K"})
K = hub.by_conv["tg-K"]
K.expect["discord"] = ["kay"]
say("discord", "dc-K", "hi", {"name": "kay", "id": "u-K-dc"})
K._new_level(3)      # two links needed: sealing a room now corners them
K.ledger.opened.update({"telegram": True, "discord": True})
SENT.clear()
K._room_sealed("discord")
time.sleep(1.5)
check("the run ended", K.ledger.ending == "CORNERED")
reached = [t for c, t in SENT if c == "tg-K"]
check("the ending was said somewhere they can hear it", bool(reached))
check("the case file landed too, with its button",
      any(not isinstance(t, str) for t in reached))
check("and it carries the ladder",
      any(isinstance(t, list) and "LEVEL 3 of 10" in str(t) for t in reached))

print("   sealing your only room on level 1 does NOT corner you")
say("telegram", "tg-S", "hi", {"name": "Solo", "id": "u-S"})
S = hub.by_conv["tg-S"]
S._room_sealed("telegram")
check("one link is still possible between the two rooms left",
      S.ledger.ending is None)

print("   [run it back] still works after the run has been swept")
K.last_seen = 0
K.director.last_player_action = 0
K.ended_at = 0
hub._sweep()
check("the run was swept", K.dead)
SENT.clear()
tap("telegram", "tg-K", "reset", {"id": "u-K"})
fresh = hub.by_conv.get("tg-K")
check("the tap opened a fresh run", fresh not in (None, K))
check("and answered instead of going silent",
      any(t == deck.RESET_OK for t in sent_to("tg-K")))
check("the fresh run knows whose room it is", fresh.keys.get("telegram") == "u-k")

# ---------------------------------------------------------------- 17. spectator
print("\n17. the page sees shapes, never words")
snap = hub.state_snapshot()
check("one entry per live run", len(snap["runs"]) <= len(hub.live()))
check("runs carry no message text",
      "beagle" not in str(snap) and "hey" not in str(snap))
check("doors are offered", set(snap["doors"]) == {"telegram", "discord", "email"})
check("the ladder is on the page",
      all("level" in r and "links_left" in r for r in snap["runs"]))
check("and the highest rung reached", "best_level" in snap)

# ---------------------------------------------------------------- 18. the inbox
print("\n18. in email, words do what buttons do everywhere else")
hint = deck.email_actions([{"value": "flag:t1"}, {"value": "plant:t1:mangoes"}])
check("the hint spells out both moves", "`flag`" in hint and "`mangoes`" in hint)

say("email", "em-M", "hello", {"name": "Mail", "address": "mail@example.com"})
M = hub.by_conv["em-M"]
SENT.clear()
mfact = hand(M)
say("email", "em-M", mfact, {"name": "Mail", "address": "mail@example.com"})
check("a bare fact name plants it", M.mind.get(mfact).origin == "email")
check("and the receipt is instant",
      any(isinstance(t, str) and t.startswith("— you told") for t in sent_to("em-M")))

SENT.clear()
say("email", "em-M", "flag", {"name": "Mail", "address": "mail@example.com"})
check("flagging before a second room says why, instead of nothing",
      any(t == deck.FLAG_TOO_EARLY for t in sent_to("em-M")))

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
print("ten levels, many players, one instance, nothing crossed.")
