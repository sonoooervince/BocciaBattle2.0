from __future__ import annotations

import pygame


class Jack:
    """Pallino fisico: dalla 0.2 può essere colpito e spostato."""

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

    @property
    def speed(self) -> float:
        return self.velocity.length()

    @property
    def is_moving(self) -> bool:
        return self.speed > 0.0

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
