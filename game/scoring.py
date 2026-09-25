from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pygame

from game.boccia import Boccia


@dataclass(frozen=True)
class EndScore:
    """Risultato di un singolo end."""

    winner: str | None
    points: int
    red_closest_px: float | None
    blue_closest_px: float | None

    def points_for(self, key: str) -> int:
        return self.points if self.winner == key else 0


def calculate_end_score(
    balls: Iterable[Boccia],
    jack_position: pygame.Vector2,
    tie_tolerance_px: float = 0.5,
) -> EndScore:
    """
    Calcola il punteggio dell'end.

    Il colore con la boccia più vicina al jack segna un punto per ogni propria
    boccia che risulta più vicina del miglior tiro avversario.
    """
    grouped: dict[str, list[float]] = {"red": [], "blue": []}

    for ball in balls:
        if ball.owner_key not in grouped:
            continue
        grouped[ball.owner_key].append(ball.position.distance_to(jack_position))

    for distances in grouped.values():
        distances.sort()

    red = grouped["red"]
    blue = grouped["blue"]

    red_best = red[0] if red else None
    blue_best = blue[0] if blue else None

    if red_best is None and blue_best is None:
        return EndScore(None, 0, None, None)

    if red_best is None:
        return EndScore("blue", len(blue), None, blue_best)

    if blue_best is None:
        return EndScore("red", len(red), red_best, None)

    if abs(red_best - blue_best) <= tie_tolerance_px:
        return EndScore(None, 0, red_best, blue_best)

    if red_best < blue_best:
        points = sum(distance < blue_best for distance in red)
        return EndScore("red", points, red_best, blue_best)

    points = sum(distance < red_best for distance in blue)
    return EndScore("blue", points, red_best, blue_best)
