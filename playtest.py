"""Offline playtest: real persona generation, no Caspian, no phone.

Simulates the opening two minutes of a run and scores two flags through
the Ledger. Two jobs:
  1. smoke-test the whole engine (structured output, provenance, verdicts)
  2. produce a 15-second transcript for the anti-slop playtest gate —
     if a stranger reads this and says "that's a bot", the voice cards fail.

Run:  .venv/bin/python playtest.py
"""

import personas
from ledger import Ledger
from mind import Mind

mind = Mind()
led = Ledger(mind)
history = {"telegram": [], "discord": [], "email": []}


def show(room, persona, turn):
    print(f"\n[{room}] {persona}: {turn.message}")
    if turn.facts_used:
        print(f"         (facts_used={turn.facts_used})")
    history[room].append({"who": "you", "text": turn.message})
    return led.record_turn(room, turn.message, turn.facts_used)


def player(room, text):
    print(f"\n[{room}] player: {text}")
    history[room].append({"who": "them", "text": text})


# --- act 1: telegram opens, a fact gets planted --------------------------
led.opened["telegram"] = True
player("telegram", "hey? who is this")
t = personas.persona_turn("maria", history["telegram"], "greet")
show("telegram", "maria", t)

player("telegram", "uh ok. day's been a mess honestly")
beagle = mind.plant("beagle", "telegram")
t = personas.persona_turn("maria", history["telegram"], "react_plant", new_fact=beagle)
show("telegram", "maria", t)

# --- discord opens, and the beagle comes back wearing a different name ---
led.opened["discord"] = True
player("discord", "hello?")
t = personas.persona_turn("deke", history["discord"], "greet")
show("discord", "deke", t)

player("discord", "do i know you")
t = personas.persona_turn("deke", history["discord"], "leak",
                          leak_facts=[beagle])
leak_turn = show("discord", "deke", t)

# --- the player flags it: provenance check, in code ----------------------
result = led.flag(leak_turn.id)
print(f"\n>> FLAG on deke's message -> {result}")
print(f">> HUD: {led.hud()}")

# --- a wrong flag, and the gaslight that follows -------------------------
player("discord", "and whats with the weather lately")
t = personas.persona_turn("deke", history["discord"], "chat")
chat_turn = show("discord", "deke", t)
result = led.flag(chat_turn.id)
print(f"\n>> FLAG on innocent message -> {result}")

led.opened["email"] = True
acc = mind.add_accusation("discord", "they accused Deke of copying someone")
t = personas.persona_turn("priya", history["email"], "gaslight",
                          leak_facts=[acc],
                          notes="they accused Deke, in another app, of saying things a stranger shouldn't know")
gas_turn = show("email", "priya", t)

result = led.flag(gas_turn.id)
print(f"\n>> FLAG on the gaslight ('we talked' is itself a leak) -> {result}")
print(f">> HUD: {led.hud()}")
print(f">> ending: {led.ending}  (NAMED needs all three rooms in one web)")
