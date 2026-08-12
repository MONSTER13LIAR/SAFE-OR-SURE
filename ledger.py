"""The Ledger: plain Python. The rules are never a vibe.

Link graph, flags, rooms alive, endings, pity-timer bookkeeping. A flag is
verified by provenance check in code — did this message use a fact the
player only ever gave a different living room? No LLM judges the player.
"""

import itertools
import time
from dataclasses import dataclass, field

import deck
from mind import Mind

ROOMS = ["telegram", "discord", "email"]

# One counter for the whole process, not per Ledger: buttons outlive runs,
# so a stale flag:tN tap must miss the new run's turns, never collide.
_TURN_COUNTER = itertools.count()


@dataclass
class Turn:
    id: str
    room: str
    text: str
    facts_used: list[str]
    ts: float
    flagged: bool = False
    flag_verdict: str | None = None  # link / old / noise
    message_id: str | None = None


@dataclass
class Ledger:
    mind: Mind
    alive: dict[str, bool] = field(default_factory=lambda: {r: True for r in ROOMS})
    opened: dict[str, bool] = field(default_factory=lambda: {r: False for r in ROOMS})
    turns: dict[str, Turn] = field(default_factory=dict)
    proven: list[frozenset] = field(default_factory=list)
    flags_left: int = 6
    wrong: int = 0
    forgiven: bool = False  # the first wrong flag is free, once per run
    ending: str | None = None  # NAMED / CORNERED / SWARMED
    _turn_counter: itertools.count = field(default_factory=lambda: _TURN_COUNTER, repr=False)
    started_at: float = field(default_factory=time.time)

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
        return len(self.email_web()) == len(ROOMS)

    def win_possible(self) -> bool:
        """Possible edges = proven links plus any pair of living rooms.
        Winning stays possible iff all rooms still fall into one
        component containing email under those edges."""
        comps = [{r} for r in ROOMS]
        edges = list(self.proven)
        living = [r for r in ROOMS if self.alive[r]]
        for i, a in enumerate(living):
            for b in living[i + 1:]:
                edges.append(frozenset((a, b)))
        for link in edges:
            merged = set()
            rest = []
            for c in comps:
                if c & link:
                    merged |= c
                else:
                    rest.append(c)
            comps = rest + [merged]
        return len(comps) == 1

    def links_left(self) -> int:
        """How many more links would finish the web. The player's only
        sense of progress — without it the middle of a run is just chatting
        with strangers and hoping."""
        return max(0, len(self._components()) - 1)

    def linked_rooms(self, room: str) -> set:
        """Rooms connected to `room` by proven links (excl. itself)."""
        for c in self._components():
            if room in c:
                return c - {room}
        return set()

    # ------------------------------------------------------------ verbs
    def flag(self, turn_id: str) -> dict:
        """Mechanical provenance check. Returns a verdict dict."""
        turn = self.turns.get(turn_id)
        if turn is None or turn.flagged:
            return {"verdict": "spent"}
        if self.ending:
            return {"verdict": "over"}
        turn.flagged = True
        self.flags_left -= 1

        new_links, old_links = [], []
        for fid in turn.facts_used:
            fact = self.mind.get(fid)
            if fact is None or fact.origin is None or fact.origin == turn.room:
                continue
            link = frozenset((fact.origin, turn.room))
            if not self.alive[fact.origin] or not self.alive[turn.room]:
                continue  # a dead room's receipts are ash
            if link in self.proven:
                old_links.append(link)
            else:
                new_links.append(link)

        if new_links:
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

        if not old_links and not self.forgiven:
            # First wrong flag of the run: free, and told why. The flag is
            # the verb the game never explains, so the first use is always
            # a guess — charging for it teaches "don't touch the button",
            # which is the opposite of the lesson. Old news still costs:
            # by then they've proved a link and know what they're doing.
            self.forgiven = True
            self.flags_left += 1
            turn.flag_verdict = "free"
            return {"verdict": "free", "ending": None}

        turn.flag_verdict = "old" if old_links else "noise"
        self.wrong += 1
        if self.wrong >= 3 or self.flags_left <= 0:
            self.ending = "SWARMED"
        return {"verdict": turn.flag_verdict, "ending": self.ending}

    def block(self, room: str) -> dict:
        if not self.alive.get(room) or self.ending:
            return {"ending": self.ending}
        self.alive[room] = False
        if not self.win_possible():
            self.ending = "CORNERED"
        return {"ending": self.ending}

    def check_flag_exhaustion(self):
        if self.ending is None and self.flags_left <= 0 and not self.won():
            self.ending = "SWARMED"
        return self.ending

    # ------------------------------------------------------------ pity timer
    def live_leaks(self) -> list[Turn]:
        """Unflagged turns that currently prove a NEW link — i.e. real,
        catchable evidence on screen right now."""
        out = []
        for t in self.turns.values():
            if t.flagged:
                continue
            for fid in t.facts_used:
                fact = self.mind.get(fid)
                if fact is None or fact.origin is None or fact.origin == t.room:
                    continue
                link = frozenset((fact.origin, t.room))
                if link in self.proven:
                    continue
                if self.alive[fact.origin] and self.alive[t.room]:
                    out.append(t)
                    break
        return out

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
        alive = sum(self.alive.values())
        return deck.hud_line(" ".join(dots), self.flags_left, alive)
