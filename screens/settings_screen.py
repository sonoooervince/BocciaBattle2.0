from __future__ import annotations

from typing import Any

import pygame

from game.ai import get_ai_profile
from game.boccia_profiles import BOCCIA_PROFILES, get_boccia_profile
from game.brands import BOCCIA_BRANDS, get_brand
from game.official_rules import SportClass, get_event_format
from game.user_settings import (
    apply_user_settings,
    runtime_user_settings,
    save_user_settings,
)


class SettingsScreen:
    """Persistent settings for official Individual gameplay."""

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
            "class",
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

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()
        title = self.font_title.render(
            "IMPOSTAZIONI UFFICIALI",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, title.get_rect(center=(width // 2, 65)))

        fmt = get_event_format(
            "individual",
            self.values["sport_class"],
        )
        labels = (
            ("Marca bocce", get_brand(self.values["preferred_brand"]).display_name),
            ("Profilo boccia", get_boccia_profile(self.values["selected_boccia_type"]).label),
            ("Livello IA", self._ai_text()),
            (
                "Classe",
                f'{self.values["sport_class"]} • {self._clock(fmt.seconds_per_side)} per end',
            ),
            ("Tempo pensiero IA", f'{self.values["ai_think_time"]:.1f} s'),
            (
                "Linee distanza",
                "ATTIVE" if self.values["show_distance_guides"] else "DISATTIVE",
            ),
            ("", "SALVA E TORNA AL MENU"),
        )

        subtitle = self.font_small.render(
            "Individuale World Boccia: 4 end • 6 bocce • tempi ufficiali per classe",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(width // 2, 105)),
        )

        self.row_rects = []
        row_width = 820
        row_height = 68
        start_y = 140
        gap = 10
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
                surface = self.font.render(
                    value,
                    True,
                    tuple(self.colors["accent"]),
                )
                self.screen.blit(surface, surface.get_rect(center=rect.center))
            else:
                left = self.font.render(
                    label,
                    True,
                    tuple(self.colors["text_secondary"]),
                )
                right = self.font.render(
                    value,
                    True,
                    tuple(self.colors["text_primary"]),
                )
                self.screen.blit(left, (rect.x + 22, rect.y + 20))
                self.screen.blit(
                    right,
                    (rect.right - right.get_width() - 22, rect.y + 20),
                )

        help_text = self.font_small.render(
            "↑↓ seleziona • ←→ modifica • INVIO conferma • ESC annulla",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            help_text,
            help_text.get_rect(center=(width // 2, height - 35)),
        )

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _ai_text(self) -> str:
        profile = get_ai_profile(self.values["ai_level"])
        return f"Lv {profile.level} • {profile.name}"

    def _change(self, direction: int) -> None:
        key = self.rows[self.selected]
        if key == "brand":
            current = get_brand(self.values["preferred_brand"])
            index = next(
                i for i, item in enumerate(BOCCIA_BRANDS)
                if item.key == current.key
            )
            self.values["preferred_brand"] = BOCCIA_BRANDS[
                (index + direction) % len(BOCCIA_BRANDS)
            ].key
        elif key == "ball":
            current = get_boccia_profile(
                self.values["selected_boccia_type"]
            )
            index = next(
                i for i, item in enumerate(BOCCIA_PROFILES)
                if item.key == current.key
            )
            self.values["selected_boccia_type"] = BOCCIA_PROFILES[
                (index + direction) % len(BOCCIA_PROFILES)
            ].key
        elif key == "ai":
            self.values["ai_level"] = max(
                1,
                min(50, self.values["ai_level"] + direction),
            )
        elif key == "class":
            classes = tuple(item.value for item in SportClass)
            index = classes.index(self.values["sport_class"])
            self.values["sport_class"] = classes[
                (index + direction) % len(classes)
            ]
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

    @staticmethod
    def _clock(seconds: int) -> str:
        minutes, remainder = divmod(int(seconds), 60)
        return f"{minutes}:{remainder:02d}"
