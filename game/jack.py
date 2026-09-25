from __future__ import annotations

import math

import pygame


class Jack:
    """Physical white target ball."""

    def __init__(
        self,
        position: pygame.Vector2,
        radius: int = 10,
        mass: float = 0.9,
    ) -> None:
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.mass = max(0.01, mass)
        self.has_entered_playing_area = False

    @property
    def speed(self) -> float:
        return self.velocity.length()

    @property
    def is_moving(self) -> bool:
        return self.speed > 0.0

    def launch(
        self,
        angle_degrees: float,
        power_percent: float,
        min_speed: float,
        max_speed: float,
    ) -> None:
        power = max(0.0, min(100.0, power_percent)) / 100.0
        speed = min_speed + (max_speed - min_speed) * power
        angle_radians = math.radians(angle_degrees)
        direction = pygame.Vector2(
            math.sin(angle_radians),
            -math.cos(angle_radians),
        )
        self.velocity = direction * speed

    def draw(self, surface: pygame.Surface) -> None:
        center = (round(self.position.x), round(self.position.y))
        pygame.draw.circle(
            surface,
            (25, 25, 25),
            (center[0] + 2, center[1] + 2),
            self.radius,
        )
        pygame.draw.circle(surface, (248, 248, 242), center, self.radius)
        pygame.draw.circle(surface, (105, 105, 105), center, self.radius, 2)
