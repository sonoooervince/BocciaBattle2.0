from __future__ import annotations

from typing import Any

import pygame

from game.player_profile import (
    apply_profile_equipment,
    load_profile,
    save_profile,
)
from game.store_catalog import REAL_BOCCIA_SETS


class StoreScreen:
    """In-game store: only verified real boccia sets."""

    PAGE_SIZE = 8

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.profile = load_profile()
        self.index = 0
        self._requested_action: str | None = None
        self.message = ""

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.font_tiny = pygame.font.SysFont("arial", 12)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(REAL_BOCCIA_SETS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(REAL_BOCCIA_SETS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._buy_or_equip()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._cycle_hardness(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._cycle_hardness(1)

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()

        title = self.font_title.render(
            "STORE • SET REALI",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (44, 30))

        info = self.font.render(
            f"GOLD {self.profile.gold}   •   RANK {self.profile.rank}",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(info, (width - info.get_width() - 44, 42))

        page_start = (self.index // self.PAGE_SIZE) * self.PAGE_SIZE
        page_items = REAL_BOCCIA_SETS[
            page_start : page_start + self.PAGE_SIZE
        ]

        y = 105
        for local_index, item in enumerate(page_items):
            global_index = page_start + local_index
            selected = global_index == self.index
            owned = self.profile.owns(item.key)
            equipped = self.profile.equipped_set == item.key

            rect = pygame.Rect(44, y, 760, 70)
            pygame.draw.rect(
                self.screen,
                tuple(self.colors["panel"]),
                rect,
                border_radius=10,
            )
            pygame.draw.rect(
                self.screen,
                tuple(
                    self.colors["accent"]
                    if selected
                    else self.colors["panel_border"]
                ),
                rect,
                3 if selected else 1,
                border_radius=10,
            )

            name = self.font.render(
                f"{item.brand_name} • {item.model}",
                True,
                tuple(self.colors["text_primary"]),
            )
            self.screen.blit(name, (rect.x + 16, rect.y + 10))

            details = self.font_small.render(
                f"{item.material} • {', '.join(item.hardnesses)}",
                True,
                tuple(self.colors["text_secondary"]),
            )
            self.screen.blit(details, (rect.x + 16, rect.y + 40))

            status = (
                "EQUIPAGGIATO"
                if equipped
                else "POSSEDUTO"
                if owned
                else f"{item.gold_cost} GOLD"
            )
            status_surface = self.font.render(
                status,
                True,
                tuple(self.colors["accent"]),
            )
            self.screen.blit(
                status_surface,
                (
                    rect.right - status_surface.get_width() - 16,
                    rect.y + 23,
                ),
            )
            y += 79

        selected = REAL_BOCCIA_SETS[self.index]
        detail_x = 835
        detail_y = 125
        self._text(
            detail_x,
            detail_y,
            selected.brand_name,
            self.font_title,
            "text_primary",
        )
        detail_y += 55
        self._text(
            detail_x,
            detail_y,
            selected.model,
            self.font,
            "accent",
        )
        detail_y += 45

        lines = (
            f"Materiale: {selected.material}",
            f"Durezze reali: {', '.join(selected.hardnesses)}",
            f"Fonte: {selected.source}",
            "",
            "Lo store non vende il prodotto reale.",
            "Il Gold sblocca solo il set virtuale.",
            "Nessun logo proprietario viene copiato.",
        )
        for line in lines:
            self._text(
                detail_x,
                detail_y,
                line,
                self.font_small,
                "text_secondary",
            )
            detail_y += 28

        if self.profile.owns(selected.key):
            detail_y += 10
            self._text(
                detail_x,
                detail_y,
                f"Durezza equipaggiata: {self.profile.equipped_hardness}",
                self.font,
                "text_primary",
            )
            detail_y += 32
            self._text(
                detail_x,
                detail_y,
                "← → cambia durezza disponibile",
                self.font_small,
                "text_secondary",
            )

        if self.message:
            self._text(
                detail_x,
                height - 115,
                self.message,
                self.font,
                "accent",
            )

        self._text(
            44,
            height - 34,
            "↑↓ scegli • INVIO compra/equipaggia • ←→ durezza • ESC menu",
            self.font_small,
            "text_secondary",
        )

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _buy_or_equip(self) -> None:
        item = REAL_BOCCIA_SETS[self.index]
        if not self.profile.owns(item.key):
            if not self.profile.purchase(item.key, item.gold_cost):
                self.message = "Gold insufficiente."
                return
            self.message = f"Sbloccato: {item.model}"

        self.profile.equip(item.key)
        save_profile(self.profile)
        apply_profile_equipment(self.settings, self.profile)
        self.message = f"Equipaggiato: {item.brand_name} {item.model}"

    def _cycle_hardness(self, direction: int) -> None:
        item = REAL_BOCCIA_SETS[self.index]
        if not self.profile.owns(item.key):
            self.message = "Prima devi sbloccare questo set."
            return
        values = item.hardnesses
        try:
            index = values.index(self.profile.equipped_hardness)
        except ValueError:
            index = 0
        self.profile.equipped_hardness = values[
            (index + direction) % len(values)
        ]
        if self.profile.equipped_set == item.key:
            save_profile(self.profile)
            apply_profile_equipment(self.settings, self.profile)

    def _text(
        self,
        x: int,
        y: int,
        value: str,
        font: pygame.font.Font,
        color_key: str,
    ) -> None:
        surface = font.render(
            value,
            True,
            tuple(self.colors[color_key]),
        )
        self.screen.blit(surface, (x, y))
