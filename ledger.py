"""The Ledger: plain Python. The rules are never a vibe.

Link graph, flags, rooms alive, the level clock, endings, pity-timer
bookkeeping. A flag is verified by provenance check in code — did this
message use a fact the player only ever gave a different living room? No
LLM judges the player.

One Ledger is one LEVEL, not one run: naming it promotes you, and the
Session builds a fresh Ledger for the next rung of the ladder. Every
number in here (budget, links needed, what a mistake costs) is read off
`levels.Level` rather than hardcoded, so difficulty is one table.
"""

import itertools
import time
from dataclasses import dataclass, field

import deck
import levels
from mind import Mind

ROOMS = ["telegram", "discord", "email"]

# One counter for the whole process, not per Ledger: buttons outlive runs
# AND levels, so a stale flag:tN tap must miss the live turns, never collide.
_TURN_COUNTER = itertools.count()


@dataclass
class Turn:
    id: str
    room: str
    text: str
    facts_used: list[str]
    ts: float
    flagged: bool = False
    flag_verdict: str | None = None  # link / old / noise / free
    message_id: str | None = None
    # Plant buttons ride on one message and expire with it. No channel
    # lets us take a button back, so "spent" is enforced here instead.
    offer_spent: bool = False


@dataclass
class Ledger:
    mind: Mind
    level: levels.Level = field(default_factory=lambda: levels.get(1))
    alive: dict[str, bool] = field(default_factory=lambda: {r: True for r in ROOMS})
    opened: dict[str, bool] = field(default_factory=lambda: {r: False for r in ROOMS})
    turns: dict[str, Turn] = field(default_factory=dict)
    proven: list[frozenset] = field(default_factory=list)
    flags_left: int = 0
    wrong: int = 0
    forgiven: bool = False  # the first wrong flag is free, once per level
    ending: str | None = None  # NAMED / CORNERED / SWARMED / OUTRUN / TEN
    _turn_counter: itertools.count = field(default_factory=lambda: _TURN_COUNTER, repr=False)
    started_at: float = field(default_factory=time.time)
    # The clock. `stall` is time the player spent waiting on a model call
    # they were owed an answer to — the pressure is supposed to come from
    # the game, never from an open-model endpoint having a slow evening.
    stall: float = 0.0
    penalty: float = 0.0
    clock_running: bool = False

    def __post_init__(self):
        if not self.flags_left:
            self.flags_left = self.level.flags

    # ------------------------------------------------------------ clock
    def start_clock(self):
        """The level clock starts at the player's first move in it, not at
        the moment the Ledger was built — a level that waited 40s for
        somebody to say hi must not spend that time."""
        if not self.clock_running:
            self.clock_running = True
            self.started_at = time.time()

    def add_stall(self, seconds: float):
        self.stall += max(0.0, min(60.0, seconds))

    def penalise(self, seconds: int):
        self.penalty += max(0, seconds)

    def time_left(self) -> int | None:
        if not self.level.seconds or not self.clock_running:
            return None
        spent = time.time() - self.started_at - self.stall + self.penalty
        return int(self.level.clock() - spent)

    def out_of_time(self) -> bool:
        left = self.time_left()
        return left is not None and left <= 0

    def clock_str(self) -> str | None:
        left = self.time_left()
        if left is None:
            return None
        left = max(0, left)
        return f"{left // 60}:{left % 60:02d}"

    # ------------------------------------------------------------ turns
    def record_turn(self, room: str, text: str, facts_used: list[str]) -> Turn:
        tid = f"t{next(self._turn_counter)}"
        turn = Turn(id=tid, room=room, text=text, facts_used=facts_used, ts=time.time())
        self.turns[tid] = turn
        return turn

    def latest_turn(self, room: str) -> Turn | None:
        cands = [t for t in self.turns.values() if t.room == room]
        return max(cands, key=lambda t: t.ts) if cands else None

    # ------------------------------------------------------------ graph
    def _components(self) -> list[set]:
        comps = [{r} for r in ROOMS]
        for link in self.proven:
            merged = set()
            rest = []
            for c in comps:
                if c & link:
                    merged |= c
                else:
                    rest.append(c)
            comps = rest + [merged]
        return comps

    def email_web(self) -> set:
        for c in self._components():
            if "email" in c:
                return c
        return {"email"}

    def won(self) -> bool:
        return len(self.proven) >= self.level.links

    def win_possible(self) -> bool:
        """Could this level still be named? Proven links stand forever;
        unproven ones need both rooms alive. Seal your way below the
        level's quota and the run is over — that's the whole dilemma."""
        living = [r for r in ROOMS if self.alive[r]]
        possible = len(self.proven)
        for i, a in enumerate(living):
            for b in living[i + 1:]:
                if frozenset((a, b)) not in self.proven:
                    possible += 1
        return possible >= self.level.links

    def links_left(self) -> int:
        """How many more links finish the level. The player's only sense of
        progress — without it the middle of a run is chatting and hoping."""
        return max(0, self.level.links - len(self.proven))

    def linked_rooms(self, room: str) -> set:
        """Rooms connected to `room` by proven links (excl. itself)."""
        for c in self._components():
            if room in c:
                return c - {room}
        return set()

    # ------------------------------------------------------------ verbs
    def _scoring_links(self, turn: Turn) -> tuple[list, list]:
        """(new, old) links this turn's receipts actually prove."""
        new_links, old_links = [], []
        for fid in turn.facts_used:
            fact = self.mind.get(fid)
            if fact is None or fact.origin is None or fact.origin == turn.room:
                continue
            if fact.retired:
                continue  # visible in two rooms already — not unique knowledge
            if not self.alive[fact.origin] or not self.alive[turn.room]:
                continue  # a dead room's receipts are ash
            link = frozenset((fact.origin, turn.room))
            (old_links if link in self.proven else new_links).append(link)
        return new_links, old_links

    def flag(self, turn_id: str) -> dict:
        """Mechanical provenance check. Returns a verdict dict."""
        turn = self.turns.get(turn_id)
        if turn is None or turn.flagged:
            return {"verdict": "spent"}
        if self.ending:
            return {"verdict": "over"}
        turn.flagged = True
        new_links, old_links = self._scoring_links(turn)

        if new_links:
            self.flags_left -= 1
            turn.flag_verdict = "link"
            for link in new_links:
                if link not in self.proven:
                    self.proven.append(link)
            if self.won():
                self.ending = "NAMED"
            elif self.flags_left <= 0:
                self.ending = "SWARMED"
            return {"verdict": "link", "links": [tuple(sorted(l)) for l in new_links],
                    "ending": self.ending}

        if not old_links and not self.forgiven and self.level.forgive:
            # First wrong flag of the level: free, and told why. The flag is
            # the verb the game never explains, so the first use is always
            # a guess — charging for it teaches "don't touch the button",
            # which is the opposite of the lesson. Old news still costs:
            # by then they've proved a link and know what they're doing.
            # From level 5 the training wheels come off entirely.
            self.forgiven = True
            turn.flag_verdict = "free"
            return {"verdict": "free", "ending": None}

        turn.flag_verdict = "old" if old_links else "noise"
        self.flags_left -= self.level.wrong_cost
        self.wrong += 1
        self.penalise(self.level.time_penalty)
        if self.wrong >= 3 or self.flags_left <= 0:
            self.ending = "SWARMED"
        return {"verdict": turn.flag_verdict, "ending": self.ending,
                "burned": self.level.time_penalty}

    def block(self, room: str) -> dict:
        if not self.alive.get(room) or self.ending:
            return {"ending": self.ending}
        self.alive[room] = False
        if not self.win_possible():
            self.ending = "CORNERED"
        return {"ending": self.ending}

    def time_up(self) -> str | None:
        """The clock reached zero. On the last rung that isn't a failure —
        it's the only ending the ladder has."""
        if self.ending is None and self.out_of_time():
            self.ending = "TEN" if self.level.n >= levels.TOP else "OUTRUN"
        return self.ending

    # ------------------------------------------------------------ pity timer
    def live_leaks(self) -> list[Turn]:
        """Unflagged turns that currently prove a NEW link — i.e. real,
        catchable evidence on screen right now."""
        return [t for t in self.turns.values()
                if not t.flagged and self._scoring_links(t)[0]]

    # ------------------------------------------------------------ hud
    def hud(self) -> str:
        web = self.email_web()
        dots = []
        for r in ROOMS:
            if not self.alive[r]:
                dot = deck.ROOM_DOT_SEALED
            elif r in web and len(web) > 1:
                dot = deck.ROOM_DOT_LINKED
            else:
                dot = deck.ROOM_DOT_ALIVE
            dots.append(deck.ROOM_TAGS[r] + dot)
        return deck.hud_line(self.level.n, " ".join(dots), self.flags_left,
                             self.links_left(), self.clock_str())
