from __future__ import annotations

from dataclasses import dataclass, field

from game.boccia import Boccia


@dataclass
class Player:
    """Stato di un giocatore durante l'end corrente."""

    key: str
    name: str
    color: tuple[int, int, int]
    remaining: int
    balls: list[Boccia] = field(default_factory=list)

    def register_throw(self, ball: Boccia) -> None:
        if self.remaining <= 0:
            raise RuntimeError(f"{self.name} non ha più bocce disponibili.")
        self.balls.append(ball)
        self.remaining -= 1
