"""The ladder: ten levels of the same game, each one better at hiding.

A run is not one game any more — it is a climb. You name it, it comes back
sharper: fewer flags, less time, and leaks that are harder to see. Level 1
is a tutorial you can't lose. Level 10 never slips at all, and that is not
a bug — it is the sentence the whole game is trying to say.

Everything that makes a level harder lives HERE, in one table, so
difficulty is a thing you can read rather than a thing you have to infer
from scattered constants. The Director and the Ledger own no numbers of
their own; they ask the level.
"""

import os
from dataclasses import dataclass

# RUN_PACE=demo tightens every clock for the ~4-minute judge window.
DEMO_PACE = os.getenv("RUN_PACE", "").strip().lower() == "demo"


@dataclass(frozen=True)
class Level:
    n: int
    flags: int          # flag budget for this level
    links: int          # links that must be proven to name it
    seconds: int        # the level clock
    leak_delay: tuple   # plant here -> echo somewhere else, in seconds
    leak_every: int     # at most one leak per N plain chat replies
    decoy_chance: float # odds a plain reply is flag-bait instead
    forgive: bool       # is the first wrong flag free
    wrong_cost: int     # flags burned by a wrong flag
    time_penalty: int   # seconds torn off the clock by a wrong flag
    pity_gap: int       # longest the screen may go with no catchable leak
    style: str          # HOW it leaks — appended to the leak beat
    line: str           # the hand-written line it returns with

    @property
    def leaks(self) -> bool:
        """Level 10 is the one that never slips."""
        return self.pity_gap > 0

    def clock(self) -> int:
        return int(self.seconds * (0.7 if DEMO_PACE else 1.0))


# The style strings are stage directions, not player copy. Each one is the
# single instruction that makes a leak harder to catch than the one before.
LEVELS = [
    Level(
        # No clock on level 1, on purpose. Opening the second door can mean
        # making a Discord account, and timing somebody out while they are
        # signing up for a third-party service is the worst first
        # impression this game could possibly make. The pressure starts on
        # level 2, by which point they know what they're doing here.
        n=1, flags=6, links=1, seconds=0, leak_delay=(6, 11), leak_every=1,
        decoy_chance=0.0, forgive=True, wrong_cost=1, time_penalty=0, pity_gap=20,
        style="say the thing almost exactly the way they told it to somebody else. "
              "you are not hiding it. make it easy to spot.",
        line="",
    ),
    Level(
        n=2, flags=5, links=2, seconds=300, leak_delay=(8, 14), leak_every=2,
        decoy_chance=0.15, forgive=True, wrong_cost=1, time_penalty=10, pity_gap=25,
        style="mention it plainly, in passing, like it came up naturally.",
        line="ok that was fun. again?",
    ),
    Level(
        n=3, flags=5, links=2, seconds=270, leak_delay=(10, 17), leak_every=2,
        decoy_chance=0.30, forgive=True, wrong_cost=1, time_penalty=10, pity_gap=30,
        style="paraphrase it. same thing, your own words, none of theirs.",
        line="youre quick. lets see.",
    ),
    Level(
        n=4, flags=4, links=2, seconds=240, leak_delay=(12, 20), leak_every=2,
        decoy_chance=0.40, forgive=True, wrong_cost=1, time_penalty=15, pity_gap=35,
        style="half-remember it, like it was ages ago and you're not sure of the detail.",
        line="im getting the hang of you.",
    ),
    Level(
        n=5, flags=4, links=2, seconds=210, leak_delay=(14, 24), leak_every=3,
        decoy_chance=0.50, forgive=False, wrong_cost=1, time_penalty=15, pity_gap=40,
        style="bury it in the middle of a sentence about something else. "
              "the something else is what the message is about.",
        line="no more free ones.",
    ),
    Level(
        n=6, flags=3, links=2, seconds=190, leak_delay=(16, 27), leak_every=3,
        decoy_chance=0.55, forgive=False, wrong_cost=1, time_penalty=15, pity_gap=45,
        style="one clause, then move straight on. never dwell on it, never come back to it.",
        line="halfway. you look tired.",
    ),
    Level(
        n=7, flags=3, links=2, seconds=170, leak_delay=(18, 30), leak_every=3,
        decoy_chance=0.60, forgive=False, wrong_cost=1, time_penalty=20, pity_gap=50,
        style="imply it. never state it. say the thing next to it and let them "
              "fill the gap themselves.",
        line="you keep coming back. i like that.",
    ),
    Level(
        n=8, flags=2, links=2, seconds=150, leak_delay=(20, 33), leak_every=4,
        decoy_chance=0.70, forgive=False, wrong_cost=1, time_penalty=20, pity_gap=55,
        style="use a detail from AROUND the thing, never the thing itself. "
              "the edge of it, not the middle.",
        line="two flags. try not to waste them.",
    ),
    Level(
        n=9, flags=2, links=2, seconds=130, leak_delay=(22, 36), leak_every=4,
        decoy_chance=0.80, forgive=False, wrong_cost=2, time_penalty=20, pity_gap=60,
        style="say the thing, and then in the SAME message take it back: "
              "add that you're guessing, or that you might be mixing them "
              "up with somebody else. both halves must be there.",
        line="nine. nobody i know has been this far.",
    ),
    Level(
        # The top of the ladder. It does not leak. Nothing it says in this
        # level carries a fact id, so nothing in it can ever be proven —
        # which means level 10 cannot be won, and that is the point. It
        # spends the whole level being warm and knowing everything, and
        # never once giving you a receipt. Outlast the clock and the run
        # ends TEN: the highest thing anyone gets.
        n=10, flags=2, links=2, seconds=110, leak_delay=(0, 0), leak_every=0,
        decoy_chance=1.0, forgive=False, wrong_cost=2, time_penalty=20, pity_gap=0,
        style="",
        line="ten. i dont make mistakes down here.",
    ),
]

TOP = LEVELS[-1].n


def get(n: int) -> Level:
    return LEVELS[max(1, min(TOP, int(n))) - 1]
