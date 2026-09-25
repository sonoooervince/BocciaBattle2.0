from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pygame

from game.boccia import Boccia


@dataclass(frozen=True)
class Measurement:
    owner_key: str
    distance_px: float
    distance_cm: float
    ball: Boccia


def pixels_to_cm(
    pixels: float,
    field_height_px: float,
    field_length_m: float = 12.5,
) -> float:
    if field_height_px <= 0:
        return 0.0
    meters = float(pixels) / float(field_height_px) * field_length_m
    return meters * 100.0


def measure_balls(
    balls: Iterable[Boccia],
    jack_position: pygame.Vector2,
    field_height_px: float,
) -> list[Measurement]:
    values = [
        Measurement(
            owner_key=ball.owner_key,
            distance_px=ball.position.distance_to(jack_position),
            distance_cm=pixels_to_cm(
                ball.position.distance_to(jack_position),
                field_height_px,
            ),
            ball=ball,
        )
        for ball in balls
    ]
    values.sort(key=lambda item: item.distance_px)
    return values


def needs_precision_measurement(
    values: list[Measurement],
    threshold_cm: float = 5.0,
) -> bool:
    if len(values) < 2:
        return False
    return abs(values[0].distance_cm - values[1].distance_cm) <= threshold_cm
