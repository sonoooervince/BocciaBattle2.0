from __future__ import annotations

import math
import random

import pygame

from game.boccia_profiles import get_boccia_profile


class Boccia:
    """Physical coloured boccia ball."""

    def __init__(
        self,
        position: pygame.Vector2,
        radius: int,
        color: tuple[int, int, int],
        owner_key: str,
        mass: float = 1.0,
        boccia_type: str = "medie",
        rolling_seed: int | None = None,
    ) -> None:
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.owner_key = owner_key
        self.mass = max(0.01, mass)
        self.boccia_profile = get_boccia_profile(boccia_type)
        self.has_entered_playing_area = False

        rng = random if rolling_seed is None else random.Random(rolling_seed)
        rolling_random = rng.uniform(
            -self.boccia_profile.rolling_variation,
            self.boccia_profile.rolling_variation,
        )
        self.friction_multiplier = max(
            0.5,
            self.boccia_profile.friction_multiplier * (1.0 + rolling_random),
        )
        self.collision_restitution = (
            self.boccia_profile.collision_restitution
        )

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

    def draw(self, surface: pygame.Surface, selected: bool = False) -> None:
        center = (round(self.position.x), round(self.position.y))
        draw_radius = max(self.radius, 4)
        shadow_offset = 2
        shadow = (center[0] + shadow_offset, center[1] + shadow_offset)
        pygame.draw.circle(surface, (24, 24, 24), shadow, draw_radius)
        pygame.draw.circle(surface, self.color, center, draw_radius)
        pygame.draw.circle(surface, (245, 245, 245), center, draw_radius, 1)

        highlight_color = tuple(
            min(255, channel + 80) for channel in self.color
        )
        highlight_radius = 2
        highlight = (
            center[0] - 2,
            center[1] - 2,
        )
        pygame.draw.circle(
            surface,
            highlight_color,
            highlight,
            highlight_radius,
        )
        if selected:
            pygame.draw.circle(
                surface,
                (250, 215, 92),
                center,
                draw_radius + 4,
                2,
            )
