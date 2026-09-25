from __future__ import annotations

from typing import Any

import pygame

from game.player_profile import load_profile, save_profile
from game.store_catalog import get_real_set


class BagScreen:
    """Configure the six real balls used by player 1 and local guest."""

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.profile = load_profile()
        self.slot = 0
        self.guest = False
        self._requested_action: str | None = None

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font = pygame.font.SysFont("arial", 21, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.slot = (self.slot - 1) % 6
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.slot = (self.slot + 1) % 6
        elif event.key == pygame.K_TAB:
            self.guest = not self.guest
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._cycle_set(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._cycle_set(1)
        elif event.key == pygame.K_q:
            self._cycle_hardness(-1)
        elif event.key == pygame.K_e:
            self._cycle_hardness(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            save_profile(self.profile)
            self._requested_action = "menu"

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()

        title = self.font_title.render(
            "BORSONE GARA",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (44, 30))

        owner = "GIOCATORE 2 (OSPITE)" if self.guest else "GIOCATORE 1"
        owner_surface = self.font.render(
            owner,
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(owner_surface, (44, 82))

        y = 135
        for index in range(6):
            spec = self.profile.get_ball_slot(index, guest=self.guest)
            item = get_real_set(spec["set_id"])
            rect = pygame.Rect(44, y, 900, 82)
            active = index == self.slot

            pygame.draw.rect(
                self.screen,
                tuple(self.colors["panel"]),
                rect,
                border_radius=12,
            )
            pygame.draw.rect(
                self.screen,
                tuple(
                    self.colors["accent"]
                    if active
                    else self.colors["panel_border"]
                ),
                rect,
                3 if active else 1,
                border_radius=12,
            )

            label = self.font.render(
                f"BOCCIA {index + 1}",
                True,
                tuple(self.colors["text_secondary"]),
            )
            name = self.font.render(
                f"{item.brand_name} • {item.model}",
                True,
                tuple(self.colors["text_primary"]),
            )
            hardness = self.font_small.render(
                f"Durezza: {spec['hardness']} • {item.material}",
                True,
                tuple(self.colors["accent"]),
            )

            self.screen.blit(label, (rect.x + 16, rect.y + 12))
            self.screen.blit(name, (rect.x + 150, rect.y + 12))
            self.screen.blit(hardness, (rect.x + 150, rect.y + 48))
            y += 92

        note = self.font_small.render(
            "←→ cambia set posseduto • Q/E cambia durezza • TAB cambia G1/G2 • INVIO salva",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(note, note.get_rect(center=(width // 2, height - 30)))

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _owned_sets(self) -> list[str]:
        return list(self.profile.owned_sets)

    def _cycle_set(self, direction: int) -> None:
        owned = self._owned_sets()
        if not owned:
            return

        spec = self.profile.get_ball_slot(self.slot, guest=self.guest)
        try:
            index = owned.index(spec["set_id"])
        except ValueError:
            index = 0

        set_id = owned[(index + direction) % len(owned)]
        item = get_real_set(set_id)
        self.profile.set_ball_slot(
            self.slot,
            set_id,
            item.hardnesses[0],
            guest=self.guest,
        )

    def _cycle_hardness(self, direction: int) -> None:
        spec = self.profile.get_ball_slot(self.slot, guest=self.guest)
        item = get_real_set(spec["set_id"])
        values = item.hardnesses

        try:
            index = values.index(spec["hardness"])
        except ValueError:
            index = 0

        hardness = values[(index + direction) % len(values)]
        self.profile.set_ball_slot(
            self.slot,
            item.key,
            hardness,
            guest=self.guest,
        )
