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
    value: str | None = None   # raw payload for meta/echo facts (name, address, phrase)
    verbatim: bool = False     # echo facts: value must be repeated word for word
    retired: bool = False      # no longer fair evidence (e.g. name visible in 2 rooms)


@dataclass
class Mind:
    """`hand` is the subset of deck.FACTS this level is played with. Every
    level deals a fresh one, so a player climbing the ladder is never
    hunting the same beagle twice — and the cards they didn't play are the
    decoy pool the level draws its flag-bait from."""

    hand: list = field(default_factory=lambda: list(deck.FACTS))
    facts: dict[str, Fact] = field(default_factory=dict)
    _acc_counter: itertools.count = field(default_factory=itertools.count, repr=False)

    def __post_init__(self):
        for fid, label, text in self.hand:
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

    def add_meta(self, fact_id: str, label: str, text: str, room: str,
                 value: str) -> Fact | None:
        """The channels leak the player before the player plants anything:
        display names, addresses. Provenance-tagged like any plant, never
        offered as a button. Mints once; later rooms don't overwrite."""
        if fact_id in self.facts:
            return None
        f = Fact(id=fact_id, label=label, text=text, origin=room,
                 planted_at=time.time(), value=value)
        self.facts[fact_id] = f
        return f

    def add_echo(self, room: str, phrase: str) -> Fact:
        """The player's own typed words, minted as evidence. Used exactly
        once per run, by the echo beat, quoted word for word."""
        fid = f"echo{next(self._acc_counter)}"
        f = Fact(id=fid, label="your own words",
                 text=deck.ECHO_TEXT.format(v=phrase), origin=room,
                 planted_at=time.time(), value=phrase, verbatim=True)
        self.facts[fid] = f
        return f

    def retire(self, fact_id: str):
        f = self.facts.get(fact_id)
        if f:
            f.retired = True

    def leakable(self) -> list[Fact]:
        """What the Director may hand out as a normal leak: planted, still
        fair, and not a verbatim quote (those go out via the echo beat only)."""
        return [f for f in self.facts.values()
                if f.origin is not None and not f.retired and not f.verbatim]

    def planted(self, room: str | None = None) -> list[Fact]:
        out = [f for f in self.facts.values() if f.origin is not None]
        if room is not None:
            out = [f for f in out if f.origin == room]
        return out

    def unplanted(self) -> list[Fact]:
        return [f for f in self.facts.values() if f.origin is None and not f.id.startswith("acc")]

    def get(self, fact_id: str) -> Fact | None:
        return self.facts.get(fact_id)
