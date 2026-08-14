"""Offline playtest: real persona generation, no Caspian, no phone.

Two jobs:
  1. smoke-test the live half of the engine — structured output,
     provenance receipts, the Ledger's verdicts;
  2. produce a transcript for the anti-slop gate. If a stranger reads
     this and says "that's a bot", the voice cards failed, not the model.

It walks the ladder rather than one level, because the whole difficulty
curve now lives in a stage direction handed to the persona: the same leak
has to be blatant on level 1, nearly invisible on level 9, and on level 10
in somebody else's mouth entirely — while still carrying its receipt. The
only way to know whether that actually happens is to read it.

Run:  .venv/bin/python playtest.py
"""

import time

import levels
import personas
from ledger import Ledger
from mind import Mind

history = {"telegram": [], "discord": [], "email": []}

_raw_turn = personas.persona_turn


def turn(*a, **kw):
    """The free endpoint drops a TLS handshake now and then. The game
    retries; so does this, or one flaky connection eats the transcript."""
    for attempt in (1, 2, 3):
        try:
            return _raw_turn(*a, **kw)
        except Exception as e:
            print(f"   (retry {attempt}: {type(e).__name__})")
            time.sleep(2)
    raise SystemExit("persona endpoint unreachable — try again later")


personas.persona_turn = turn


def show(led, room, persona, turn):
    print(f"\n[{room}] {persona}: {turn.message}")
    if turn.facts_used:
        print(f"         (facts_used={turn.facts_used})")
    history[room].append({"who": "you", "text": turn.message})
    return led.record_turn(room, turn.message, turn.facts_used)


def player(room, text):
    print(f"\n[{room}] player: {text}")
    history[room].append({"who": "them", "text": text})


def level_ledger(n):
    mind = Mind()
    led = Ledger(mind, level=levels.get(n))
    for r in led.opened:
        led.opened[r] = True
    return mind, led


# --- level 1: it barely tries to hide ------------------------------------
print("=" * 62)
print("LEVEL 1 — it says the thing almost exactly as you said it")
print("=" * 62)
mind, led = level_ledger(1)
lvl = levels.get(1)

player("telegram", "hey? who is this")
show(led, "telegram", "maria", turn("maria", history["telegram"], "greet"))

player("telegram", "uh ok. days been a mess honestly")
beagle = mind.plant("beagle", "telegram")
show(led, "telegram", "maria",
     turn("maria", history["telegram"], "react_plant", new_fact=beagle))

player("discord", "hello?")
show(led, "discord", "deke", turn("deke", history["discord"], "greet"))

player("discord", "do i know you")
t = turn("deke", history["discord"], "leak",
                          leak_facts=[beagle], notes=lvl.style)
leak_turn = show(led, "discord", "deke", t)

result = led.flag(leak_turn.id)
print(f"\n>> FLAG -> {result}")
print(f">> HUD: {led.hud()}")
print(f">> one link names level 1: ending={led.ending}")

# --- level 5: the same fact, buried --------------------------------------
print("\n" + "=" * 62)
print("LEVEL 5 — the same leak, buried mid-sentence")
print("=" * 62)
mind, led = level_ledger(5)
lvl = levels.get(5)
rice = mind.plant("rice", "telegram")
player("discord", "whats going on with you")
t = turn("deke", history["discord"], "leak",
                          leak_facts=[rice], notes=lvl.style)
show(led, "discord", "deke", t)
print(f">> did it still carry the receipt? {'yes' if 'rice' in t.facts_used else 'NO — the leak was lost'}")

# --- level 9: said and waved off in the same breath ----------------------
print("\n" + "=" * 62)
print("LEVEL 9 — said, then waved off like a guess")
print("=" * 62)
mind, led = level_ledger(9)
lvl = levels.get(9)
mangoes = mind.plant("mangoes", "telegram")
player("email", "anything new")
t = turn("priya", history["email"], "leak",
                          leak_facts=[mangoes], notes=lvl.style)
show(led, "email", "priya", t)
print(f">> did it still carry the receipt? {'yes' if 'mangoes' in t.facts_used else 'NO — the leak was lost'}")

# --- the decoy: looks like a leak, provably isn't ------------------------
print("\n" + "=" * 62)
print("THE DECOY — flag-bait that is not evidence")
print("=" * 62)
bait = mind.get("printer")
player("discord", "you around")
t = turn("deke", history["discord"], "decoy", notes=bait.text)
decoy_turn = show(led, "discord", "deke", t)
print(f">> facts_used must be empty: {t.facts_used!r}")
print(f">> flagging it -> {led.flag(decoy_turn.id)}")

# --- level 10: it slips, wearing somebody else's name --------------------
print("\n" + "=" * 62)
print("LEVEL 10 — it slips, in somebody else's name")
print("=" * 62)
# The whole rung rests on this: the hardest stage direction in the game
# tells the persona to hand the player's own detail to a third party. If
# the model drops the fact id while doing that, the receipt is gone and
# level 10 stops being winnable by accident rather than by design.
mind, led = level_ledger(levels.TOP)
lvl = levels.get(levels.TOP)
bianchi = mind.plant("bianchi", "telegram")
player("discord", "hey whats up")
t = turn("deke", history["discord"], "leak", leak_facts=[bianchi], notes=lvl.style)
leak10 = show(led, "discord", "deke", t)
print(f">> did it still carry the receipt? "
      f"{'yes' if 'bianchi' in t.facts_used else 'NO — level 10 would be unwinnable'}")
print(f">> flagging it -> {led.flag(leak10.id)}")
print(f">> HUD: {led.hud()}   (one link down, one flag left, no margin)")

print("\n-- and the bait down here costs both flags at once --")
mind2, led2 = level_ledger(levels.TOP)
bait10 = mind2.get("nightshift")
player("telegram", "you still up")
t = turn("maria", history["telegram"], "decoy", notes=bait10.text)
d10 = show(led2, "telegram", "maria", t)
print(f">> facts_used must be empty: {t.facts_used!r}")
print(f">> flagging it -> {led2.flag(d10.id)}")

# --- the beat that restarts a level -------------------------------------
print("\n" + "=" * 62)
print("RESUME — it comes back as if nothing happened")
print("=" * 62)
show(led, "telegram", "maria",
     turn("maria", history["telegram"], "resume"))
