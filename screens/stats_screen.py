from __future__ import annotations

from typing import Any

import pygame

from game.player_profile import load_profile
from game.store_catalog import get_real_set


class StatsScreen:
    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.profile = load_profile()

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        self.font = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)

    def handle_event(self, event: pygame.event.Event) -> None:
        del event

    def update(self, dt: float) -> None:
        del dt
        self.profile = load_profile()

    def draw(self) -> None:
        self.screen.fill(tuple(self.colors["background"]))
        width, height = self.screen.get_size()

        title = self.font_title.render(
            "STATISTICHE",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (44, 30))

        summary = (
            f"RANK {self.profile.rank} • LV {self.profile.level} • "
            f"RATING {self.profile.rating}"
        )
        self._line(44, 90, summary, self.font_big, "accent")

        matches = self.profile.wins + self.profile.losses
        win_rate = 0.0 if matches == 0 else self.profile.wins / matches * 100.0
        average = self.profile.average_distance_cm
        average_text = "—" if average is None else f"{average:.1f} cm"

        rows = (
            ("Partite", str(matches)),
            ("Vittorie / sconfitte", f"{self.profile.wins} / {self.profile.losses}"),
            ("Win rate", f"{win_rate:.1f}%"),
            ("Tiri registrati", str(self.profile.shots)),
            ("Accosti entro 25 cm", f"{self.profile.approach_25_rate * 100:.1f}%"),
            ("Accosti entro 50 cm", f"{self.profile.approach_50_rate * 100:.1f}%"),
            ("Bocciate con contatto", str(self.profile.bocciate_hits)),
            ("Jack colpiti", str(self.profile.jack_hits)),
            ("Distanza media dal jack", average_text),
            ("Serie vittorie", str(self.profile.streak)),
        )

        y = 145
        for label, value in rows:
            rect = pygame.Rect(44, y, 650, 48)
            pygame.draw.rect(
                self.screen,
                tuple(self.colors["panel"]),
                rect,
                border_radius=9,
            )
            self._line(rect.x + 14, rect.y + 13, label, self.font, "text_secondary")
            value_surface = self.font.render(
                value,
                True,
                tuple(self.colors["text_primary"]),
            )
            self.screen.blit(
                value_surface,
                (rect.right - value_surface.get_width() - 14, rect.y + 13),
            )
            y += 54

        self._line(735, 145, "PER SET REALE", self.font_big, "text_primary")
        y2 = 190
        ranked = sorted(
            self.profile.set_stats.items(),
            key=lambda pair: int(pair[1].get("shots", 0)),
            reverse=True,
        )[:8]

        if not ranked:
            self._line(
                735,
                y2,
                "Gioca qualche partita per raccogliere dati.",
                self.font_small,
                "text_secondary",
            )
        else:
            for set_id, values in ranked:
                item = get_real_set(set_id)
                shots = int(values.get("shots", 0))
                matches_for_set = int(values.get("matches", 0))
                wins = int(values.get("wins", 0))
                distance_sum = float(values.get("distance_sum_cm", 0.0))
                avg = "—" if shots == 0 else f"{distance_sum / shots:.1f} cm"

                self._line(
                    735,
                    y2,
                    f"{item.brand_name} • {item.model}",
                    self.font,
                    "accent",
                )
                y2 += 24
                self._line(
                    735,
                    y2,
                    (
                        f"{matches_for_set} match • {wins} W • "
                        f"{shots} tiri • media {avg}"
                    ),
                    self.font_small,
                    "text_secondary",
                )
                y2 += 48

        footer = self.font_small.render(
            "ESC = torna al menu",
            True,
            tuple(self.colors["text_secondary"]),
        )
        self.screen.blit(
            footer,
            footer.get_rect(center=(width // 2, height - 28)),
        )

    def _line(
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
