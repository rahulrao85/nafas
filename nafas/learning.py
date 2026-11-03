"""Per-person learning: which actions actually help *this* person.

Thompson sampling over a Beta(helped, didn't help) per action. Simple, explainable, and it
keeps trying alternatives instead of repeating the first thing that worked once.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .actions import Action


@dataclass
class ActionStats:
    helped: int = 0
    not_helped: int = 0

    @property
    def tries(self) -> int:
        return self.helped + self.not_helped


@dataclass
class Learner:
    prior_a: float = 1.0
    prior_b: float = 1.0
    stats: dict[str, ActionStats] = field(default_factory=dict)

    def record(self, action_id: str, helped: bool) -> None:
        s = self.stats.setdefault(action_id, ActionStats())
        if helped:
            s.helped += 1
        else:
            s.not_helped += 1

    def score(self, action_id: str) -> float:
        s = self.stats.get(action_id, ActionStats())
        return (self.prior_a + s.helped) / (self.prior_a + self.prior_b + s.tries)

    def choose(self, candidates: list[Action], rng: random.Random, exclude: set[str] = frozenset()) -> Action | None:
        pool = [a for a in candidates if a.id not in exclude]
        if not pool:
            return None
        def draw(a: Action) -> float:
            s = self.stats.get(a.id, ActionStats())
            return rng.betavariate(self.prior_a + s.helped, self.prior_b + s.not_helped)
        return max(pool, key=draw)

    def summary(self) -> list[dict]:
        return sorted(
            ({"action_id": k, "helped": v.helped, "not_helped": v.not_helped,
              "score": round(self.score(k), 2)} for k, v in self.stats.items()),
            key=lambda r: -r["score"])
