from __future__ import annotations

from typing import Any

import pygame

from game.ai import get_ai_profile
from game.tournament import TournamentProgress, TournamentSession
from screens.game_screen import GameScreen


class TournamentScreen:
    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        self.screen = screen
        self.settings = settings
        self.colors = settings["colors"]
        self.session = TournamentSession()
        self.game = self._create_game()
        self.progress: TournamentProgress | None = None
        self._requested_action: str | None = None
        self.font = pygame.font.SysFont("arial", 17, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.game.state == self.game.MATCH_RESULT:
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_n,
                ):
                    self._continue_after_result()
                return
            if event.key == pygame.K_r:
                return
        self.game.handle_event(event)

    def update(self, dt: float) -> None:
        self.game.update(dt)
        if (
            self.game.state == self.game.MATCH_RESULT
            and self.progress is None
        ):
            winner_key = self.game.match.winner
            if winner_key is not None:
                tournament_winner = (
                    "red"
                    if winner_key == self.game.human_key
                    else "blue"
                )
                self.progress = self.session.record_match(
                    tournament_winner
                )

    def draw(self) -> None:
        self.game.draw()
        self._draw_tournament_banner()
        if (
            self.game.state == self.game.MATCH_RESULT
            and self.progress is not None
        ):
            human_score = self.game.match.total_scores[self.game.human_key]
            ai_score = self.game.match.total_scores[self.game.ai_key]
            self.game.results.draw_tournament_result(
                progress=self.progress,
                total_rounds=self.session.total_rounds,
                total_scores={"red": human_score, "blue": ai_score},
            )

    def consume_action(self) -> str | None:
        action = self._requested_action
        self._requested_action = None
        return action

    def _create_game(self) -> GameScreen:
        game = GameScreen(self.screen, self.settings)
        game.ai.set_level(self.session.current_bot_level)
        return game

    def _continue_after_result(self) -> None:
        if self.progress is None:
            return
        if self.progress.status == "advanced":
            self.session.prepare_next_match()
            self.progress = None
            self.game = self._create_game()
            return
        self._requested_action = "menu"

    def _draw_tournament_banner(self) -> None:
        current_round = self.session.current_round
        profile = get_ai_profile(current_round.bot_level)
        rect = pygame.Rect(54, 40, 350, 62)
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["panel"]),
            rect,
            border_radius=11,
        )
        pygame.draw.rect(
            self.screen,
            tuple(self.colors["accent"]),
            rect,
            2,
            border_radius=11,
        )
        title = self.font.render(
            f"TORNEO • ROUND {current_round.round_number}/{self.session.total_rounds}",
            True,
            tuple(self.colors["text_primary"]),
        )
        self.screen.blit(title, (rect.x + 12, rect.y + 8))
        detail = self.font_small.render(
            f"IA Lv {current_round.bot_level} • {profile.name}",
            True,
            tuple(self.colors["accent"]),
        )
        self.screen.blit(detail, (rect.x + 12, rect.y + 36))
