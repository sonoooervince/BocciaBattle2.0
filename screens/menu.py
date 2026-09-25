from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from game.player_profile import load_profile


@dataclass(frozen=True)
class MenuItem:
    label: str
    action: str | None
    enabled: bool = True
    note: str = ""


class MenuScreen:
    """Menu principale semplice e pronto per nuove modalità."""

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.font_title = pygame.font.SysFont("arial", 54, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 20)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("arial", 15)
        self.profile = load_profile()

        self.items = (
            MenuItem("GIOCA VS COMPUTER", "quick"),
            MenuItem(
                "TORNEO SETTIMANALE",
                "tournament",
                note="7 round • IA livello 5 → 50",
            ),
            MenuItem("ALLENAMENTO", "training", note="tiri liberi e bersagli"),
            MenuItem("STORE", "store", note="solo set di bocce reali"),
            MenuItem("IMPOSTAZIONI", "settings", note="classe, IA e controllo"),
            MenuItem("ESCI", "quit"),
        )
        self.selected_index = 0
        self.button_rects: list[pygame.Rect] = []
        self._requested_action: str | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_selected()

        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos) and self.items[index].enabled:
                    self.selected_index = index
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = index
                    self._activate_selected()
                    break

    def update(self, dt: float) -> None:
        del dt

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()

        title = self.font_title.render(
            "BOCCIA BATTLE",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, title.get_rect(center=(width // 2, 115)))

        subtitle = self.font_subtitle.render(
            "Fisica • Strategia • Precisione",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(width // 2, 158)),
        )

        self.profile = load_profile()
        profile_text = self.font_small.render(
            (
                f"RANK {self.profile.rank} • LV {self.profile.level} • "
                f"XP {self.profile.xp} • GOLD {self.profile.gold}"
            ),
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            profile_text,
            profile_text.get_rect(center=(width // 2, 190)),
        )

        self.button_rects = []
        button_width = 520
        button_height = 62
        start_y = 220
        gap = 12

        for index, item in enumerate(self.items):
            rect = pygame.Rect(
                (width - button_width) // 2,
                start_y + index * (button_height + gap),
                button_width,
                button_height,
            )
            self.button_rects.append(rect)

            selected = index == self.selected_index and item.enabled
            fill = tuple(self.colors["panel"])
            border = tuple(
                self.colors["accent"]
                if selected
                else self.colors["panel_border"]
            )
            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(
                self.screen,
                border,
                rect,
                3 if selected else 1,
                border_radius=14,
            )

            text_color = tuple(
                self.colors["text_primary"]
                if item.enabled
                else self.colors["text_secondary"]
            )
            label = self.font_button.render(item.label, True, text_color)
            self.screen.blit(label, (rect.x + 24, rect.y + 15))

            if item.note:
                note_text = item.note.upper() if not item.enabled else item.note
                note = self.font_small.render(
                    note_text,
                    True,
                    tuple(
                        self.colors["accent"]
                        if item.enabled
                        else self.colors["text_secondary"]
                    ),
                )
                self.screen.blit(
                    note,
                    (rect.right - note.get_width() - 22, rect.y + 28),
                )

        footer = self.font_small.render(
            "↑ ↓ / W S = scegli   •   INVIO = conferma   •   ESC = esci",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            footer,
            footer.get_rect(center=(width // 2, height - 36)),
        )

        version = self.font_small.render(
            "VERSIONE 0.9",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(version, (18, height - 30))

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _move_selection(self, direction: int) -> None:
        count = len(self.items)
        for _ in range(count):
            self.selected_index = (self.selected_index + direction) % count
            if self.items[self.selected_index].enabled:
                return

    def _activate_selected(self) -> None:
        item = self.items[self.selected_index]
        if item.enabled and item.action is not None:
            self._requested_action = item.action
