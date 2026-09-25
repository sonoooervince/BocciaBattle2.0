from __future__ import annotations

from typing import Any

import pygame

from game.scoring import EndScore
from game.tournament import TournamentProgress


class ResultScreen:
    def __init__(
        self,
        screen: pygame.Surface,
        colors: dict[str, Any],
    ) -> None:
        self.screen = screen
        self.colors = colors
        self.font_title = pygame.font.SysFont("arial", 38, bold=True)
        self.font_big = pygame.font.SysFont("arial", 27, bold=True)
        self.font = pygame.font.SysFont("arial", 20)
        self.font_small = pygame.font.SysFont("arial", 16)

    def draw_end_result(
        self,
        end_number: int,
        score: EndScore,
        total_scores: dict[str, int],
        winner_name: str | None,
        is_tiebreak: bool,
    ) -> None:
        del winner_name
        title = (
            f"TIE-BREAK {max(1, end_number - 4)} COMPLETATO"
            if is_tiebreak
            else f"END {end_number} COMPLETATO"
        )
        if score.red_points == score.blue_points:
            message = "Punteggio in parità"
        elif score.red_points > score.blue_points:
            message = "Segna il ROSSO"
        else:
            message = "Segna il BLU"

        secondary = (
            "Il tie-break decide solo il vincitore"
            if is_tiebreak
            else (
                f"TOTALE  ROSSO {total_scores['red']}  •  "
                f"BLU {total_scores['blue']}"
            )
        )
        self._draw_overlay(
            title=title,
            message=message,
            primary_value=f"{score.red_points}  -  {score.blue_points}",
            secondary_value=secondary,
            hint="INVIO / SPAZIO / N  →  continua",
        )

    def draw_match_result(
        self,
        total_scores: dict[str, int],
        winner_name: str,
        total_ends: int,
    ) -> None:
        self._draw_overlay(
            title="PARTITA TERMINATA",
            message=f"Vince {winner_name}",
            primary_value=(
                f"{total_scores['red']}  -  {total_scores['blue']}"
            ),
            secondary_value=f"End disputati: {total_ends}",
            hint="INVIO / SPAZIO / R  →  nuova partita",
        )

    def draw_tournament_result(
        self,
        progress: TournamentProgress,
        total_rounds: int,
        total_scores: dict[str, int],
    ) -> None:
        score_text = f"{total_scores['red']}  -  {total_scores['blue']}"
        if progress.status == "advanced":
            title = f"ROUND {progress.completed_round} SUPERATO"
            message = f"Battuta IA livello {progress.bot_level}"
            secondary = (
                f"Prossimo: Round {progress.next_round}/{total_rounds} "
                f"• IA Lv {progress.next_bot_level}"
            )
            hint = "INVIO / SPAZIO / N  →  prossimo round"
        elif progress.status == "champion":
            title = "TORNEO COMPLETATO"
            message = "BOCCIA BATTLE CHAMPION"
            secondary = f"Superati tutti i {total_rounds} round"
            hint = "INVIO / SPAZIO  →  torna al menu"
        else:
            title = f"ELIMINATO AL ROUND {progress.completed_round}"
            message = f"Vince IA livello {progress.bot_level}"
            secondary = "Il torneo termina qui"
            hint = "INVIO / SPAZIO  →  torna al menu"
        self._draw_overlay(
            title=title,
            message=message,
            primary_value=score_text,
            secondary_value=secondary,
            hint=hint,
        )

    def draw_message(
        self,
        title: str,
        message: str,
        detail: str,
        hint: str,
    ) -> None:
        self._draw_overlay(
            title=title,
            message=message,
            primary_value=detail,
            secondary_value="",
            hint=hint,
        )

    def _draw_overlay(
        self,
        title: str,
        message: str,
        primary_value: str,
        secondary_value: str,
        hint: str,
    ) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((7, 10, 14, 188))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(
            (self.screen.get_width() - 620) // 2,
            (self.screen.get_height() - 330) // 2,
            620,
            330,
        )
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["panel"]),
            rect,
            border_radius=18,
        )
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["accent"]),
            rect,
            2,
            border_radius=18,
        )
        self._center(
            self.font_title.render(
                title,
                True,
                tuple(self.colors["text_primary"]),
            ),
            rect.centery - 110,
        )
        self._center(
            self.font_big.render(
                message,
                True,
                tuple(self.colors["accent"]),
            ),
            rect.centery - 48,
        )
        self._center(
            self.font_title.render(
                primary_value,
                True,
                tuple(self.colors["text_primary"]),
            ),
            rect.centery + 12,
        )
        if secondary_value:
            self._center(
                self.font.render(
                    secondary_value,
                    True,
                    tuple(self.colors["text_secondary"]),
                ),
                rect.centery + 68,
            )
        self._center(
            self.font_small.render(
                hint,
                True,
                tuple(self.colors["text_secondary"]),
            ),
            rect.centery + 123,
        )

    def _center(self, surface: pygame.Surface, center_y: int) -> None:
        rect = surface.get_rect(
            center=(self.screen.get_width() // 2, center_y)
        )
        self.screen.blit(surface, rect)
