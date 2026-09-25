from __future__ import annotations

import pygame


class Jack:
    """Il pallino. Nella 0.1 è statico; diventerà fisico nella 0.2."""

    def __init__(self, position: pygame.Vector2, radius: int = 10) -> None:
        self.position = pygame.Vector2(position)
        self.radius = radius

    def draw(self, surface: pygame.Surface) -> None:
        center = (round(self.position.x), round(self.position.y))
        pygame.draw.circle(surface, (25, 25, 25), (center[0] + 2, center[1] + 2), self.radius)
        pygame.draw.circle(surface, (248, 248, 242), center, self.radius)
        pygame.draw.circle(surface, (105, 105, 105), center, self.radius, 2)
