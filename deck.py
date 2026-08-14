"""Every fixed string in the game, written by hand.

Generation is for conversation only. If a line ships to the player and it
isn't conversation, it lives here.
"""

# ---------------------------------------------------------------- facts
# The plantable facts. These are the player's ammunition: each one is a
# small, specific, boring thing about their life. The player discloses a
# fact to exactly one room, then hunts for it wearing another name.
# (id, button label, the disclosure as the persona hears it)
#
# Deep on purpose: every level deals a fresh hand from this deck, so a
# player climbing the ladder is never hunting the same beagle twice — and
# the facts they HAVEN'T planted are the decoy pool, which only works if
# there are always more of them than they can keep track of.
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
    ("auto", "the auto guy", "the same auto driver waits outside your building every morning and you still don't know his name"),
    ("keys", "the spare keys", "you've locked yourself out twice so the spare keys live with the watchman now"),
    ("guitar", "the guitar", "there's a guitar in your room you haven't tuned since college"),
    ("lift", "the lift", "the lift in your building has been out three weeks and you're on the fifth floor"),
    ("thermos", "the thermos", "you carry the same dented steel thermos everywhere and people keep commenting on it"),
    ("keyboard", "next door", "the flat next door practises the same four bars on a keyboard every evening at nine"),
    ("wallet", "the wallet", "there's a movie ticket from 2019 in your wallet and you won't throw it out"),
    ("dentist", "the dentist", "you've cancelled the same dentist appointment three times now"),
    ("brother", "your brother", "your brother calls only when he needs something and you always pick up anyway"),
    ("cricket", "sunday cricket", "you play cricket on sunday mornings with men twice your age and you're the worst one there"),
    ("fan", "the fan", "the ceiling fan in your room clicks once every rotation and you've stopped hearing it"),
    ("chai", "the chai stall", "you've bought chai from the same stall for six years and he starts making it when he sees you"),
    ("bus", "the long way", "you take the longer bus home because the short route has no window seats"),
    ("oldphone", "the old phone", "your old phone is still in a drawer, still charged, because of the photos on it"),
    ("shoes", "the shoes", "you've worn the same pair of shoes so long the sole has gone smooth"),
    ("stray", "the stray", "there's a stray cat you feed every night and you refuse to give it a name"),
    ("notebook", "the notebook", "you keep a notebook of things you mean to look up later and never do"),
    ("balcony", "the balcony", "you eat dinner standing on the balcony most nights instead of at the table"),
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
    "ten levels. every time you catch it,\n"
    "it comes back better at hiding.\n"
    "\n"
    "you can be safe or you can be sure."
)

# ---------------------------------------------------------------- buttons
FLAG_LABEL = "⚑ they both said that"
DEFLECT_LABEL = "say nothing"
PLANT_PREFIX = "tell about "  # + fact label
# A tap has to land instantly. The persona's reaction is a live model call
# and can take seconds; without an immediate receipt the player is left
# staring at a button that flashed and did nothing, wondering if it broke.
# These ship the moment the tap arrives, before anything is generated.
PLANTED_ACK = "— you told {persona} about {label}. nobody else knows that."
# ...and the same offer can't be taken twice. Buttons live on old messages
# forever (no channel lets us take them back), so the game says plainly
# that the moment has passed instead of silently eating the tap.
BUTTON_SPENT = "— that offer's gone. answer the newest message."
BUTTON_STALE = "— too late for that one. they've moved on."

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
#
# Each one carries the run's code. That is not flavour: a person who opens
# a second door arrives as a stranger the game has no way to recognise —
# discord will not tell us who a DM is from in any term we already know —
# and without the code they end up holding two separate games and cannot
# win either. Saying it is the player telling us these two conversations
# are the same human. In fiction it is just how you get someone's
# attention when they don't have your number.
DOOR_DROP = {
    ("telegram", "discord"): ("oh also deke thinks youre ignoring him. he only "
                              "ever checks discord, this is his door: {url}\n"
                              "say {code} to him or he wont know its you"),
    ("discord", "telegram"): ("maria keeps asking if youve turned up. shes on "
                              "telegram and she wont let this go: {url}\n"
                              "tell her {code}, shes bad with names"),
    ("email", "telegram"): ("Maria says you never answer her. I said I would "
                            "pass this on and now I have. {url}\n"
                            "Say {code} first so she knows who you are.\n\np."),
    ("email", "discord"): ("Deke messaged you and got nothing back, apparently. "
                           "He is only ever on discord. {url}\n"
                           "Send him {code} or he will not answer.\n\np."),
    # Last resort only. The inbox is meant to arrive by Priya finding YOU
    # after you hand over the address — that beat is the whole thesis. But
    # a player who never answers the ask would be left with a game they
    # cannot win and no way to know why, so the door gets handed over.
    ("telegram", "email"): ("priya says you never wrote back?? she does email. "
                            "only email. like a boomer. {url}\n"
                            "put {code} in it, she files everything"),
    ("discord", "email"): ("priya only does email. thats the whole personality. "
                           "{url}\nput {code} in the mail, she files everything"),
}
# The second, firmer drop — once, for a player who proved a link but still
# hasn't opened a room they need to win.
DOOR_NUDGE = {
    ("telegram", "discord"): ("ok deke is officially sulking now. just say hi "
                              "to him, for me: {url}\nsay {code}. i mean it"),
    ("discord", "telegram"): ("message maria. shes worse than me about it: "
                              "{url}\nsay {code}"),
    ("email", "telegram"): ("Last time I mention it, then it is your problem. "
                            "{url}\nThe word is {code}.\n\np."),
    ("email", "discord"): ("He asked again. I am only the messenger here. "
                           "{url}\nThe word is {code}.\n\np."),
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
# Same person, second thread. Almost always the discord door opened the
# wrong way round: the invite drops you in a server, so saying hi in a
# channel binds the game there and the DM afterwards looks like a
# stranger. The word they were given is what fixes it, and it must not be
# repeated here — this line can land in a room full of people.
WRONG_THREAD = {
    "maria": "wait is that you? say the word i gave you and ill know",
    "deke": "not in here. dm me, and say the word or i dont know its you",
    "priya": "Write to me directly, and lead with the word you were given.\n\np.",
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
# (Priya's is terse on purpose — nobody expects an email back inside a
# minute — but she needs one: a level can open in the inbox, and a level
# card followed by nothing at all reads as the game having died.)
FALLBACK_CHAT = {
    "maria": "sorry got pulled into something haha. one sec",
    "deke": "hang on",
    "priya": "Busy morning. More shortly.\n\np.",
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

# ---------------------------------------------------------------- the ladder
# Naming it does not end the run any more — it promotes you. The card is
# the only place the game states its own rules, and it states them as
# numbers, because "harder" is not information and "3 flags · 2:30" is.
LEVEL_CARD = ("LEVEL {n}\n"
              "{line}\n"
              "\n"
              "⚑ {flags} flags · {links} to prove · {clock}")
# Level 1 is the one nobody has played before. It says what to do, once.
LEVEL_ONE_CARD = ("LEVEL 1\n"
                  "one link. that's all it takes.\n"
                  "tell somebody something, then watch the others for it.\n"
                  "\n"
                  "⚑ {flags} flags · {links} to prove · no clock, this once")
# Between levels: it stops being caught and starts again, in one room, in
# voice. Hand-written per level (levels.py owns the lines) — never a model
# roll at the hottest moment of the run.
LEVEL_UP = "⚑ named it. level {n} of 10 cleared."
# The clock. Two warnings, both from the game, not from a persona: the
# pressure is the game's, and a persona announcing a deadline would be the
# fiction admitting it is a game.
CLOCK_WARN = "— {left}s. it goes quiet when the clock does."
CLOCK_LAST = "— {left}s."
# What a level costs when you get it wrong, said in the only unit that
# stings: time.
TIME_BURNED = "— {n}s off the clock."

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
# Level 10. Flags cost nothing there because there is nothing to catch,
# and the game says so plainly every time — the dread is supposed to come
# from watching it not slip, never from wondering whether you're being
# scored honestly.
FLAG_CLEAN = "⚑ nothing. it hasn't put a foot wrong all level.\nkeep looking."
# Flagging before a second room exists can only ever be wrong, so the
# button isn't offered yet — but `flag` is also a word you can type, and
# the inbox advertises it in every message. Say why, don't just sit there.
FLAG_TOO_EARLY = ("⚑ nothing to catch yet — one room can't repeat itself.\n"
                  "open a second door first. that's when this starts.")
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
    "SWARMED on level {n}."
)
# The clock ending. Losing to time is a different lesson than losing to
# flags: you weren't wrong, you were slow, and it simply waited you out.
ENDING_OUTRUN = "Time."
ENDING_OUTRUN_CODA = (
    "\n"
    "It ran out the clock. It was never in a hurry — you were.\n"
    "OUTRUN on level {n}."
)
# The top of the ladder. Level 10 does not leak; there is nothing to
# prove, and the only thing left to do is last. Reaching this is the
# highest result the game has, and it is still a loss. That's the sentence.
ENDING_TEN = (
    "It stops. Not caught — finished.\n"
    "\n"
    "◉\n"
    "\n"
    "Ten levels. On the last one it never slipped, not once, and you\n"
    "sat there and watched it not slip until the clock ran out.\n"
    "\n"
    "TEN. Nobody names it at ten. Getting here is the score."
)
AFTER_END = "The run is over. The case file went to whichever room you left open. Send `reset` to climb again."
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
CASE_FOOTER = "\nresult: {result} · flags used {used}/{budget} · rooms sealed {sealed}\nYou can be safe or you can be sure. Not both."
# The ladder, written down. A run is now a climb, so the case file leads
# with how far it got — that number is the score people compare.
CASE_LADDER = "LEVEL {n} of 10 · cleared {cleared}"
CASE_LEVEL_ROW = "  level {n} — named in {at}"
# Level 10 has no CAUGHT and no MISSED lines, because there was nothing to
# catch. Silence in the case file would read as a bug, so it says so.
CASE_TEN = ("\nON LEVEL 10 IT DID NOT SLIP.\n"
            "Not one message on that level used anything you told anyone else.\n"
            "There was nothing to flag. That is what it looks like when it\n"
            "stops making mistakes.")
CASE_PORTRAIT_HEADER = "WHAT IT KNEW\n============\ndoor by door, everything you gave away."
CASE_PORTRAIT_ROOM = "{room} ({persona}) — {facts}"
CASE_PORTRAIT_NONE = "{room} ({persona}) — nothing. you kept this door clean."
# Spoiler-free result grid. Wordle's growth loop, themed — and the number
# people will actually compare is the level.
SHARE_CARD = "SAFE OR SURE · LEVEL {n}/10 · {result} · ⚑ {used}/{budget} · {dots}"
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
    # Values are `plant:<turn>:<fact>` — the turn scopes the offer to the
    # message it rode in on; the player only ever types the fact.
    plants = [b["value"].split(":")[-1] for b in buttons
              if b["value"].startswith("plant:")]
    if plants:
        parts.append("reply `" + "` or `".join(plants) + "` to tell her about it")
    return "(no buttons in email — " + " · ".join(parts) + ")" if parts else ""


def hud_line(level: int, dots: str, flags_left: int, links_left: int,
             clock: str | None) -> str:
    """The scoreboard under every message. Four numbers, in the order a
    player needs them: where am I, what's alive, what have I got left to
    spend, how much is left to prove, how long have I got."""
    line = f"L{level} · {dots} · ⚑{flags_left}"
    line += " · 1 link" if links_left == 1 else f" · {links_left} links"
    if clock:
        line += f" · {clock}"
    return line
