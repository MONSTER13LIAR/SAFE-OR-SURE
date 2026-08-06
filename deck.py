"""Every fixed string in the game, written by hand.

Generation is for conversation only. If a line ships to the player and it
isn't conversation, it lives here.
"""

# ---------------------------------------------------------------- facts
# The plantable facts. These are the player's ammunition: each one is a
# small, specific, boring thing about their life. The player discloses a
# fact to exactly one room, then hunts for it wearing another name.
# (id, button label, the disclosure as the persona hears it)
FACTS = [
    ("beagle", "the beagle", "the neighbour's beagle keeps digging under the fence and turning up in your kitchen"),
    ("bianchi", "the bianchi", "you're rebuilding a 1989 Bianchi road bike in the middle of your kitchen"),
    ("rice", "the rice", "you've burned rice twice this week in the new cooker"),
    ("nightshift", "night shifts", "you got moved to night shifts this month and your sleep is wrecked"),
    ("mangoes", "the mangoes", "there's a whole crate of mangoes ripening on your balcony"),
    ("tap", "the tap", "your landlord still hasn't fixed the bathroom tap and it drips all night"),
    ("chess", "chess guy", "you lose to the same guy at online chess every single night"),
    ("jacket", "the jacket", "you lost your denim jacket at a wedding last month and you're still not over it"),
    ("moneyplant", "the plant", "your money plant is dying no matter what you try"),
    ("cousin", "the cousin", "your cousin is camped on your couch while she studies for her exams"),
    ("printer", "the printer", "you bought a secondhand printer that only prints in blue"),
    ("pigeons", "the pigeons", "pigeons nest in your AC unit and wake you at six every morning"),
]

# ---------------------------------------------------------------- buttons
FLAG_LABEL = "⚑ they both said that"
DEFLECT_LABEL = "deflect"
PLANT_PREFIX = "tell about "  # + fact label

# ---------------------------------------------------------------- cold open
# First contact when the game reaches out to YOU. Hand-written: the hook
# beat happens before any model call, instantly and in-voice. Telegram
# can't initiate cold (platform rule) — Maria's room is the entry door.
COLD_OPEN = {
    "discord": "hey its deke. you never answer anywhere else so lets try here",
    "email": (
        "hi. priya here. we overlapped last year, you'd remember the "
        "tuesday trains if nothing else. how is the new place.\n\np."
    ),
}

# ---------------------------------------------------------------- fixed beats
# First block ever: a surviving room sends this, verbatim, seconds later.
SEAL_FIRST = "felt good, didn't it."

# The NAMED collapse: each living room stops MID-SENTENCE (ordinary
# unfinished sentences, never glitch-text), three seconds of nothing,
# then the card.
NAMED_CUT = {
    "telegram": "wait haha ok so the thing about the",
    "discord": "anyway the",
    "email": "so. about the",
}

# ---------------------------------------------------------------- flag results
LINKED = "⚑ LINKED — {a} and {b} are the same thing."
LINKED_FIRST = "⚑ LINKED — {a} and {b} are the same thing.\nIt noticed you noticed."
FLAG_OLD_NEWS = "⚑ burned. You already proved that."
FLAG_NOISE = "⚑ burned. That one actually was a coincidence."
FLAG_SPENT = "already flagged."
DEFLECTED = "you keep it to yourself."

# ---------------------------------------------------------------- endings
ENDING_NAMED = (
    "It stops mid-sentence. All of them, at once.\n"
    "\n"
    "◉\n"
    "\n"
    "Three rooms. Three names. One thing, and you proved it.\n"
    "YOU NAMED IT."
)
ENDING_CORNERED = (
    "Quiet, finally. Every door you could seal is sealed.\n"
    "\n"
    "This one has no block button. It knows you know that.\n"
    "\n"
    "CORNERED. You made yourself safe by making sure impossible."
)
# CORNERED enumerates, deterministically, what each block burned. Losing
# must decode to specific choices — that's the replay trigger.
CORNERED_BURNED_HEADER = "what died with the doors:"
CORNERED_BURNED = "you told {persona} about {fact}. nobody can prove that now."
ENDING_SWARMED = "You were never sure."
ENDING_SWARMED_CODA = (
    "\n"
    "Out of flags. It isn't angry. It just stopped pretending.\n"
    "SWARMED."
)
AFTER_END = "The run is over — your inbox has the case file. Send `reset` to go again."
RESET_OK = "fresh. say hi somewhere."

# ---------------------------------------------------------------- case file
CASE_SUBJECT = "case file — safe or sure"
CASE_HEADER = "CASE FILE\n=========\nEvery time it slipped, and what you did about it.\n"
CASE_CAUGHT = "CAUGHT   {room}: used {fact} (you only told {origin})"
CASE_MISSED = "MISSED   {room}: used {fact} (you only told {origin}) — it was right there"
CASE_WRONG = "BURNED   you flagged {room} over nothing"
CASE_FOOTER = "\nresult: {result} · flags used {used}/6 · rooms sealed {sealed}\nYou can be safe or you can be sure. Not both."
CASE_PORTRAIT_HEADER = "WHAT IT KNEW\n============\ndoor by door, everything you gave away."
CASE_PORTRAIT_ROOM = "{room} ({persona}) — {facts}"
CASE_PORTRAIT_NONE = "{room} ({persona}) — nothing. you kept this door clean."
# Spoiler-free result grid. Wordle's growth loop, themed.
SHARE_CARD = "SAFE OR SURE · {result} · ⚑ {used}/6 · {dots}"
RUN_IT_BACK = "run it back"

# ---------------------------------------------------------------- hud
ROOM_DOT_LINKED = "◉"
ROOM_DOT_ALIVE = "◌"
ROOM_DOT_SEALED = "✕"


def hud_line(dots: str, flags_left: int, alive: int) -> str:
    return f"{dots} · ⚑ {flags_left} · {alive} rooms up"
