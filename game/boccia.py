from __future__ import annotations

import math

import pygame


class Boccia:
    """Una boccia con posizione e velocità in coordinate 2D."""

    def __init__(
        self,
        position: pygame.Vector2,
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.color = color

    @property
    def speed(self) -> float:
        return self.velocity.length()

    @property
    def is_moving(self) -> bool:
        return self.speed > 0.0

    def reset(self, position: pygame.Vector2) -> None:
        self.position.update(position)
        self.velocity.update(0, 0)

    def launch(
        self,
        angle_degrees: float,
        power_percent: float,
        min_speed: float,
        max_speed: float,
    ) -> None:
        """
        Lancia la boccia.

        0° = perfettamente verso l'alto.
        Valori negativi = sinistra, positivi = destra.
        """
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

        shadow_offset = max(2, self.radius // 5)
        shadow = (center[0] + shadow_offset, center[1] + shadow_offset)
        pygame.draw.circle(surface, (25, 25, 25), shadow, self.radius)

        pygame.draw.circle(surface, self.color, center, self.radius)
        pygame.draw.circle(surface, (245, 245, 245), center, self.radius, 2)

        highlight_radius = max(2, self.radius // 4)
        highlight = (
            center[0] - self.radius // 3,
            center[1] - self.radius // 3,
        )
        pygame.draw.circle(surface, (255, 170, 170), highlight, highlight_radius)
