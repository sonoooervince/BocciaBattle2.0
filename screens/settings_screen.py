from __future__ import annotations

from typing import Any

import pygame

from game.ai import get_ai_profile
from game.boccia_profiles import BOCCIA_PROFILES, get_boccia_profile
from game.brands import BOCCIA_BRANDS, get_brand
from game.user_settings import (
    apply_user_settings,
    runtime_user_settings,
    save_user_settings,
)


class SettingsScreen:
    """Impostazioni locali persistenti di Boccia Battle."""

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.values = runtime_user_settings(settings)
        self.selected = 0
        self._requested_action: str | None = None

        self.font_title = pygame.font.SysFont("arial", 44, bold=True)
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("arial", 15)
        self.row_rects: list[pygame.Rect] = []

        self.rows = (
            "brand",
            "ball",
            "ai",
            "ends",
            "think",
            "guides",
            "save",
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.rows)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.rows)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._change(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._change(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.rows[self.selected] == "save":
                    self._save()
                else:
                    self._change(1)

        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.row_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.row_rects):
                if not rect.collidepoint(event.pos):
                    continue
                self.selected = index
                if self.rows[index] == "save":
                    self._save()
                else:
                    direction = -1 if event.pos[0] < rect.centerx else 1
                    self._change(direction)
                break

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()

        title = self.font_title.render(
            "IMPOSTAZIONI",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, title.get_rect(center=(width // 2, 72)))

        subtitle = self.font_small.render(
            "Le preferenze vengono salvate localmente sul PC.",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(width // 2, 108)),
        )

        self.row_rects = []
        row_width = 760
        row_height = 67
        start_y = 145
        gap = 10

        labels = (
            ("Marca bocce", self._brand_text()),
            ("Profilo boccia", self._ball_text()),
            ("Livello IA", self._ai_text()),
            ("End partita", str(self.values["match_ends"])),
            ("Tempo IA", f'{self.values["ai_think_time"]:.1f} s'),
            (
                "Linee distanza",
                "ATTIVE" if self.values["show_distance_guides"] else "DISATTIVE",
            ),
            ("", "SALVA E TORNA AL MENU"),
        )

        for index, (label, value) in enumerate(labels):
            rect = pygame.Rect(
                (width - row_width) // 2,
                start_y + index * (row_height + gap),
                row_width,
                row_height,
            )
            self.row_rects.append(rect)
            active = index == self.selected

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

            if index == len(labels) - 1:
                text = self.font.render(
                    value,
                    True,
                    tuple(self.colors["accent"]),
                )
                self.screen.blit(text, text.get_rect(center=rect.center))
                continue

            label_surface = self.font.render(
                label,
                True,
                tuple(self.colors["text_secondary"]),
            )
            value_surface = self.font.render(
                value,
                True,
                tuple(self.colors["text_primary"]),
            )
            self.screen.blit(label_surface, (rect.x + 22, rect.y + 20))
            self.screen.blit(
                value_surface,
                (
                    rect.right - value_surface.get_width() - 22,
                    rect.y + 20,
                ),
            )

        help_text = self.font_small.render(
            "↑↓ seleziona • ←→ modifica • INVIO conferma • ESC annulla",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            help_text,
            help_text.get_rect(center=(width // 2, height - 48)),
        )

        source = self.font_small.render(
            "Marche: produttori approvati World Boccia 2025–2028 • nomi testuali, nessun logo",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(
            source,
            source.get_rect(center=(width // 2, height - 24)),
        )

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _brand_text(self) -> str:
        return get_brand(self.values["preferred_brand"]).display_name

    def _ball_text(self) -> str:
        return get_boccia_profile(
            self.values["selected_boccia_type"]
        ).label

    def _ai_text(self) -> str:
        profile = get_ai_profile(self.values["ai_level"])
        return f'Lv {profile.level} • {profile.name}'

    def _change(self, direction: int) -> None:
        key = self.rows[self.selected]

        if key == "brand":
            current = get_brand(self.values["preferred_brand"])
            index = next(
                i for i, brand in enumerate(BOCCIA_BRANDS)
                if brand.key == current.key
            )
            self.values["preferred_brand"] = BOCCIA_BRANDS[
                (index + direction) % len(BOCCIA_BRANDS)
            ].key

        elif key == "ball":
            current = get_boccia_profile(
                self.values["selected_boccia_type"]
            )
            index = next(
                i for i, profile in enumerate(BOCCIA_PROFILES)
                if profile.key == current.key
            )
            self.values["selected_boccia_type"] = BOCCIA_PROFILES[
                (index + direction) % len(BOCCIA_PROFILES)
            ].key

        elif key == "ai":
            self.values["ai_level"] = max(
                1,
                min(50, self.values["ai_level"] + direction),
            )

        elif key == "ends":
            self.values["match_ends"] = max(
                1,
                min(8, self.values["match_ends"] + direction),
            )

        elif key == "think":
            self.values["ai_think_time"] = round(
                max(
                    0.2,
                    min(
                        2.0,
                        self.values["ai_think_time"] + direction * 0.1,
                    ),
                ),
                1,
            )

        elif key == "guides":
            self.values["show_distance_guides"] = not self.values[
                "show_distance_guides"
            ]

    def _save(self) -> None:
        save_user_settings(self.values)
        new_settings = apply_user_settings(self.settings, self.values)
        self.settings.clear()
        self.settings.update(new_settings)
        self._requested_action = "menu"
