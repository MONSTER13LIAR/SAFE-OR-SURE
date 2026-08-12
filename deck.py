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

# ---------------------------------------------------------------- the frame
# The one piece of out-of-fiction text in the whole game, and it earns its
# place: a stranger who taps a link with no idea what this is has no way to
# infer the rules from the inside. Playtest 2026-08-12: without this, the
# first tap is the flag button on message one, which cannot be right yet.
# Sent once, in the room they walked in through, before anyone says hello.
OPENING_CARD = (
    "three people are about to message you\n"
    "on three different apps.\n"
    "\n"
    "they are one thing.\n"
    "\n"
    "tell them things. when one of them knows\n"
    "something you only told somebody else,\n"
    "tap ⚑.\n"
    "\n"
    "you can be safe or you can be sure."
)

# ---------------------------------------------------------------- buttons
FLAG_LABEL = "⚑ they both said that"
DEFLECT_LABEL = "say nothing"
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

# ---------------------------------------------------------------- metadata facts
# What the channels give away about the player for free, minted as
# provenance-tagged facts the moment a room sees them. This is the ammo a
# player who never taps a plant button still gets hunted with.
META_NAME_LABEL = "your name"
META_NAME_TEXT = ('their name is "{v}". you know it and may use it, but '
                  "sparingly, and never as the first word of a message")
META_EMAIL_LABEL = "your email address"
META_EMAIL_TEXT = "their email address is {v}"
# The verbatim echo: the player's own typed words, in another mouth.
ECHO_TEXT = 'they once typed, in another app, exactly this: "{v}"'

# The rooms hand out each other's doors — the README is not the
# onboarding, the conversation is. Whichever room the player found first
# becomes their guide, so every one of these is somebody's first line.
# Keyed (the room talking, the room it's handing over).
DOOR_DROP = {
    ("telegram", "discord"): ("oh also deke thinks youre ignoring him. he only "
                              "ever checks discord, this is his door: {url}"),
    ("discord", "telegram"): ("maria keeps asking if youve turned up. shes on "
                              "telegram and she wont let this go: {url}"),
    ("email", "telegram"): ("Maria says you never answer her. I said I would "
                            "pass this on and now I have. {url}\n\np."),
    ("email", "discord"): ("Deke messaged you and got nothing back, apparently. "
                           "He is only ever on discord. {url}\n\np."),
    # Last resort only. The inbox is meant to arrive by Priya finding YOU
    # after you hand over the address — that beat is the whole thesis. But
    # a player who never answers the ask would be left with a game they
    # cannot win and no way to know why, so the door gets handed over.
    ("telegram", "email"): ("priya says you never wrote back?? she does email. "
                            "only email. like a boomer. {url}"),
    ("discord", "email"): "priya only does email. thats the whole personality. {url}",
}
# The second, firmer drop — once, for a player who proved a link but still
# hasn't opened a room they need to win.
DOOR_NUDGE = {
    ("telegram", "discord"): ("ok deke is officially sulking now. just say hi "
                              "to him, for me: {url}"),
    ("discord", "telegram"): "message maria. shes worse than me about it: {url}",
    ("email", "telegram"): ("Last time I mention it, then it is your problem. "
                            "{url}\n\np."),
    ("email", "discord"): ("He asked again. I am only the messenger here. "
                           "{url}\n\np."),
}

# ---------------------------------------------------------------- fixed beats
# First block ever: a surviving room sends this, verbatim, seconds later.
SEAL_FIRST = "felt good, didn't it."

# Somebody else talking in the same thread — a server channel, a cc'd
# mail. Said once, to them, in voice: this is a conversation for two.
NOT_IN_PUBLIC = {
    "maria": "haha hi. this is a bit public though, message me directly?",
    "deke": "not in here. dm me",
    "priya": "There are more people on this thread than I thought. Write to me directly.\n\np.",
}

# Every seat taken: the game is full, not broken. Said once, kindly.
BUSY = "too many people in here at once. give it a few minutes and say hi again."

# Model-down fallbacks: if generation fails twice on a load-bearing beat,
# these ship instead of silence. In voice, hand-written.
FALLBACK_GREET = {
    "maria": "heyy finally. was starting to think you lost this number haha. hows your day been",
    "deke": "took you long enough.",
    "priya": "you found the inbox. good. how is the new place.\n\np.",
}
FALLBACK_ESCALATE = {
    "maria": "heyy you went quiet\nhaha rude\nanyway. miss you",
    "deke": "you alive\nk",
    "priya": "quiet week. hope the new place is being kind to you.\n\np.",
}
# When the player has just said something and the model is late, silence
# reads as a broken game. A distracted half-answer reads as a person.
# (No email line: nobody expects an email back inside a minute.)
FALLBACK_CHAT = {
    "maria": "sorry got pulled into something haha. one sec",
    "deke": "hang on",
}
# Asked point-blank whether it's real. Silence here is the worst possible
# answer — it reads as a caught-out machine, which is the one thing it
# never is.
FALLBACK_DENY = {
    "maria": "haha what. no. why is that a question",
    "deke": "no",
    "priya": "No. Odd question.\n\np.",
}
# The two asks that carry the game's plumbing: if the model is late, ask
# plainly rather than not at all. Priya never asks for an email (she IS
# the inbox), so she only has the discord line.
FALLBACK_ASK_EMAIL = {
    "maria": "whats your email btw, i wanna send you the thing",
    "deke": "whats your email. easier to send it there",
}
FALLBACK_ASK_HANDLE = {
    "maria": "whats your discord name btw",
    "priya": "What is your discord name. I was asked to ask.\n\np.",
}

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
# Progress, stated in the only unit that matters. A player mid-run has no
# way to feel how close the end is, and "am I getting anywhere" is the
# question that decides whether they keep going.
PROGRESS_ONE = "one more like that and it's over."
PROGRESS_MANY = "{n} more links like that and it's over."
FLAG_OLD_NEWS = "⚑ burned. You already proved that pair — it's the room you haven't linked yet that costs you."
FLAG_NOISE = "⚑ burned. Nothing in that one came from another room.\nWait until somebody knows a thing you only told somebody else."
# The first wrong flag is free, and says why — a player learns this verb by
# using it, and the first use is always a guess. Costing them a flag for
# touching the only button on screen is how the game taught "don't play".
FLAG_FREE = ("⚑ that one was just talk — nothing in it came from another room.\n"
             "on the house, this once. flag one of them for knowing something\n"
             "you only told somebody else.")
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
# Sealed in before ever finding the inbox: the same loss, honestly told.
# The line about the unblockable room would be a lie here — they never
# opened it, so nothing is waiting in it.
ENDING_CORNERED_NO_INBOX = (
    "Quiet, finally. Every door you found, you shut.\n"
    "\n"
    "There was one you never opened. Nothing can reach you now, and\n"
    "nothing can be proved either.\n"
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
# The harvest timeline: only shown when the player handed over the address
# themselves and the cold open used it. The point of the whole game, dated.
CASE_HARVEST = ("LEAKED   {gave}: you told {persona} your email address\n"
                "         {used}: priya used it. you leaked first")
CASE_CAUGHT = "CAUGHT   {room}: used {fact} (you only told {origin})"
CASE_MISSED = "MISSED   {room}: used {fact} (you only told {origin}) — on your screen at {at}. it was right there"
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
# Which dot is which app — a stranger should never have to memorize order.
ROOM_TAGS = {"telegram": "tg", "discord": "dc", "email": "em"}


def email_actions(buttons) -> str:
    """Mail clients strip interactive buttons — every tap the inbox offers
    is invisible there, so the same moves are spelled out as words to
    reply with. The email room is act 3 and the only unblockable one; a
    player must never be stuck watching it with no move available."""
    parts = []
    if any(b["value"].startswith("flag:") for b in buttons):
        parts.append("reply `flag` to call this message out")
    plants = [b["value"].split(":", 1)[1] for b in buttons
              if b["value"].startswith("plant:")]
    if plants:
        parts.append("reply `" + "` or `".join(plants) + "` to tell her about it")
    return "(no buttons in email — " + " · ".join(parts) + ")" if parts else ""


def hud_line(dots: str, flags_left: int, alive: int) -> str:
    return f"{dots} · ⚑ {flags_left} left · {alive} rooms up"
