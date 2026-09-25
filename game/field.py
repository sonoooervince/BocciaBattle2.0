from __future__ import annotations

import pygame


class Field:
    """Geometria e disegno del campo di Boccia Battle."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.launch_line_y = rect.bottom - 112
        self.launch_point = pygame.Vector2(rect.centerx, self.launch_line_y + 54)
        self.jack_default_position = pygame.Vector2(rect.centerx + 70, rect.top + 185)

    @property
    def playable_bounds(self) -> pygame.Rect:
        return self.rect.copy()

    def draw(self, surface: pygame.Surface) -> None:
        # Ombra del campo
        shadow_rect = self.rect.move(7, 8)
        pygame.draw.rect(surface, (18, 23, 28), shadow_rect, border_radius=14)

        # Fondo campo
        pygame.draw.rect(surface, (67, 118, 92), self.rect, border_radius=14)

        # Fasce leggere per dare profondità senza texture esterne
        stripe_height = 62
        y = self.rect.top
        alternate = False
        while y < self.rect.bottom:
            stripe = pygame.Rect(self.rect.left, y, self.rect.width, min(stripe_height, self.rect.bottom - y))
            if alternate:
                overlay = pygame.Surface(stripe.size, pygame.SRCALPHA)
                overlay.fill((255, 255, 255, 10))
                surface.blit(overlay, stripe.topleft)
            alternate = not alternate
            y += stripe_height

        # Bordo
        pygame.draw.rect(surface, (230, 236, 232), self.rect, 3, border_radius=14)

        # Zona del giocatore
        player_zone = pygame.Rect(
            self.rect.left + 3,
            self.launch_line_y,
            self.rect.width - 6,
            self.rect.bottom - self.launch_line_y - 3,
        )
        zone_overlay = pygame.Surface(player_zone.size, pygame.SRCALPHA)
        zone_overlay.fill((20, 45, 72, 90))
        surface.blit(zone_overlay, player_zone.topleft)

        # Linea di lancio
        pygame.draw.line(
            surface,
            (250, 215, 92),
            (self.rect.left + 8, self.launch_line_y),
            (self.rect.right - 8, self.launch_line_y),
            4,
        )

        # Indicatore posizione iniziale
        pygame.draw.circle(
            surface,
            (250, 215, 92),
            (round(self.launch_point.x), round(self.launch_point.y)),
            24,
            2,
        )

        # Piccolo asse centrale di riferimento
        pygame.draw.line(
            surface,
            (126, 160, 143),
            (self.rect.centerx, self.rect.top + 10),
            (self.rect.centerx, self.launch_line_y - 10),
            1,
        )
