from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pygame

from game.boccia import Boccia


@dataclass(frozen=True)
class EndScore:
    red_points: int
    blue_points: int
    red_closest_px: float | None
    blue_closest_px: float | None
    penalty_red: int = 0
    penalty_blue: int = 0

    @property
    def winner(self) -> str | None:
        if self.red_points > self.blue_points:
            return "red"
        if self.blue_points > self.red_points:
            return "blue"
        return None

    @property
    def points(self) -> int:
        return max(self.red_points, self.blue_points)

    def points_for(self, key: str) -> int:
        return self.red_points if key == "red" else self.blue_points


def calculate_end_score(
    balls: Iterable[Boccia],
    jack_position: pygame.Vector2,
    tie_tolerance_px: float = 0.5,
    penalty_points: dict[str, int] | None = None,
) -> EndScore:
    grouped: dict[str, list[float]] = {"red": [], "blue": []}

    for ball in balls:
        if ball.owner_key in grouped:
            grouped[ball.owner_key].append(
                ball.position.distance_to(jack_position)
            )

    for distances in grouped.values():
        distances.sort()

    red = grouped["red"]
    blue = grouped["blue"]
    red_best = red[0] if red else None
    blue_best = blue[0] if blue else None
    red_points = 0
    blue_points = 0

    if red_best is None and blue_best is None:
        pass
    elif red_best is None:
        blue_points = len(blue)
    elif blue_best is None:
        red_points = len(red)
    elif abs(red_best - blue_best) <= tie_tolerance_px:
        closest = min(red_best, blue_best)
        red_points = sum(
            abs(distance - closest) <= tie_tolerance_px for distance in red
        )
        blue_points = sum(
            abs(distance - closest) <= tie_tolerance_px for distance in blue
        )
    elif red_best < blue_best:
        red_points = sum(
            distance < blue_best - tie_tolerance_px for distance in red
        )
    else:
        blue_points = sum(
            distance < red_best - tie_tolerance_px for distance in blue
        )

    penalties = penalty_points or {}
    penalty_red = max(0, int(penalties.get("red", 0)))
    penalty_blue = max(0, int(penalties.get("blue", 0)))
    red_points += penalty_red
    blue_points += penalty_blue

    return EndScore(
        red_points=red_points,
        blue_points=blue_points,
        red_closest_px=red_best,
        blue_closest_px=blue_best,
        penalty_red=penalty_red,
        penalty_blue=penalty_blue,
    )
