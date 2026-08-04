"""The Mind: one shared memory store for all personas.

Every fact the player reveals is tagged with the room they said it in.
Provenance is the whole game — a fact's origin room is what makes a
cross-room reuse of it provable evidence.
"""

import itertools
import time
from dataclasses import dataclass, field

import deck


@dataclass
class Fact:
    id: str
    label: str
    text: str
    origin: str | None = None  # room the player disclosed it in; None = unplanted
    planted_at: float = 0.0


@dataclass
class Mind:
    facts: dict[str, Fact] = field(default_factory=dict)
    _acc_counter: itertools.count = field(default_factory=itertools.count, repr=False)

    def __post_init__(self):
        for fid, label, text in deck.FACTS:
            self.facts[fid] = Fact(id=fid, label=label, text=text)

    def plant(self, fact_id: str, room: str) -> Fact | None:
        f = self.facts.get(fact_id)
        if f is None or f.origin is not None:
            return None
        f.origin = room
        f.planted_at = time.time()
        return f

    def add_accusation(self, room: str, text: str) -> Fact:
        """A wrong flag becomes a fact of its own — 'we talked about you'
        is itself a cross-channel leak a sharp player can flag."""
        fid = f"acc{next(self._acc_counter)}"
        f = Fact(id=fid, label="the accusation", text=text, origin=room, planted_at=time.time())
        self.facts[fid] = f
        return f

    def planted(self, room: str | None = None) -> list[Fact]:
        out = [f for f in self.facts.values() if f.origin is not None]
        if room is not None:
            out = [f for f in out if f.origin == room]
        return out

    def unplanted(self) -> list[Fact]:
        return [f for f in self.facts.values() if f.origin is None and not f.id.startswith("acc")]

    def get(self, fact_id: str) -> Fact | None:
        return self.facts.get(fact_id)
