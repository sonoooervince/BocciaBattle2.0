from __future__ import annotations

from typing import Any

import pygame

from game.boccia_profiles import (
    BOCCIA_PROFILES,
    cycle_boccia_profile,
)
from game.match import MatchController
from game.player_profile import load_profile
from game.store_catalog import approximate_profile_key
from game.official_rules import PENALTY_BALL_SECONDS, WARMUP_SECONDS, other_side
from screens.game_screen import GameScreen


class LocalGameScreen(GameScreen):
    """Two-player hot-seat mode using the same official rules engine."""

    def __init__(self, screen: pygame.Surface, settings: dict[str, Any]) -> None:
        super().__init__(
            screen,
            settings,
            progression_enabled=False,
        )
        self.local_coin_winner = self.random.choice(("p1", "p2"))
        self.player1_key = "red"
        self.player2_key = "blue"
        self.human_key = "red"
        self.ai_key = "__none__"
        self.timeout_owner: str | None = None
        self.local_profile = load_profile()
        self.state = self.COIN_CHOICE
        self.coin_toss_text = (
            "GIOCATORE 1 ha vinto il sorteggio"
            if self.local_coin_winner == "p1"
            else "GIOCATORE 2 ha vinto il sorteggio"
        )
        self.referee_message = self.coin_toss_text

    def handle_event(self, event: pygame.event.Event) -> None:
        if (
            self.state == self.COIN_CHOICE
            and event.type == pygame.KEYDOWN
        ):
            if event.key == pygame.K_r:
                self._local_choose_colour("red")
            elif event.key == pygame.K_b:
                self._local_choose_colour("blue")
            return

        if (
            self.state == self.TIMEOUT
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_f
        ):
            owner = self.timeout_owner or self.match.current_key
            if owner is not None:
                self.match.forfeit(owner)
            self.state = self.MATCH_RESULT
            return

        super().handle_event(event)

    def draw(self) -> None:
        super().draw()
        if self.state == self.COIN_CHOICE:
            winner = (
                "GIOCATORE 1"
                if self.local_coin_winner == "p1"
                else "GIOCATORE 2"
            )
            self.results.draw_message(
                "SORTEGGIO LOCALE",
                f"{winner} sceglie il colore",
                "R = ROSSO    B = BLU",
                "L'altro giocatore riceve automaticamente l'altro colore",
            )

    def _local_choose_colour(self, winner_colour: str) -> None:
        loser_colour = other_side(winner_colour)
        if self.local_coin_winner == "p1":
            self.player1_key = winner_colour
            self.player2_key = loser_colour
        else:
            self.player2_key = winner_colour
            self.player1_key = loser_colour

        self.human_key = self.player1_key
        self.ai_key = "__none__"
        self.match = self._create_local_match()
        self.jack = self._new_jack_at_cross()
        self.referee_message = (
            f"G1 {self.player1_key.upper()} • "
            f"G2 {self.player2_key.upper()}"
        )
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.state = self.WARMUP

    def _create_local_match(self) -> MatchController:
        red_name = (
            "GIOCATORE 1"
            if self.player1_key == "red"
            else "GIOCATORE 2"
        )
        blue_name = (
            "GIOCATORE 1"
            if self.player1_key == "blue"
            else "GIOCATORE 2"
        )
        return MatchController(
            balls_per_player=self.event_format.balls_per_side,
            red_color=tuple(self.colors["red_ball"]),
            blue_color=tuple(self.colors["blue_ball"]),
            max_ends=self.event_format.ends,
            tie_tolerance_px=self.match_settings["tie_tolerance_px"],
            red_name=red_name,
            blue_name=blue_name,
            seconds_per_side=self.event_format.seconds_per_side,
        )

    def _restart_match(self) -> None:
        self.local_coin_winner = self.random.choice(("p1", "p2"))
        self.player1_key = "red"
        self.player2_key = "blue"
        self.match = self._create_local_match()
        self.jack = self._new_jack_at_cross()
        self.state = self.COIN_CHOICE
        self.warmup_remaining = float(WARMUP_SECONDS)
        self.coin_toss_text = (
            "GIOCATORE 1 ha vinto il sorteggio"
            if self.local_coin_winner == "p1"
            else "GIOCATORE 2 ha vinto il sorteggio"
        )
        self.referee_message = self.coin_toss_text
        self.penalty_ball = None
        self._reset_end_counters()

    def _make_ball(self, key: str, ai: bool = False):
        del ai
        player = self.match.player(key)
        slot_index = max(
            0,
            min(
                5,
                self.event_format.balls_per_side - player.remaining,
            ),
        )
        guest = key == self.player2_key
        spec = self.local_profile.get_ball_slot(
            slot_index,
            guest=guest,
        )
        from game.boccia import Boccia

        return Boccia(
            self.field.launch_point_for(key),
            radius=self.gameplay["boccia_radius"],
            color=player.color,
            owner_key=key,
            mass=self.gameplay["boccia_mass"],
            boccia_type=approximate_profile_key(spec["hardness"]),
            set_id=spec["set_id"],
            hardness=spec["hardness"],
        )

    def _prepare_jack_turn(self) -> None:
        if self.match.current_key is None:
            return
        self.angle = 0.0
        self.power = 48.0
        self.active_ball = None
        self.state = self.JACK_READY

    def _prepare_coloured_turn(self) -> None:
        player = self.match.current_player
        if player is None:
            self._finish_end()
            return
        self.angle = 0.0
        self.power = 55.0
        self.active_ball = self._make_ball(player.key)
        self.ai_plan = None
        self.state = self.READY

    def _prepare_penalty_attempt(self) -> None:
        key = self.match.current_key
        if key is None:
            self.penalty_ball = None
            self._finalize_end_score()
            return

        self.angle = 0.0
        self.power = 45.0
        self.penalty_time_remaining = float(PENALTY_BALL_SECONDS)
        self.penalty_announced = set()
        self.penalty_ball = self._make_ball(key)
        self.referee_message = (
            f"One minute! Penalty ball a {self.match.player(key).name}"
        )
        self.state = self.PENALTY_READY

    def _human_can_aim(self) -> bool:
        return (
            self.match.current_key is not None
            and self.state in (
                self.READY,
                self.JACK_READY,
                self.PENALTY_READY,
            )
        )

    def _launch_human(self) -> None:
        key = self.match.current_key
        if key is None:
            return

        if self.state == self.PENALTY_READY:
            if self.penalty_ball is None:
                return
            self._capture_legitimate_state()
            self.penalty_ball.launch(
                self.angle,
                self.power,
                self.gameplay["min_launch_speed"],
                self.gameplay["max_launch_speed"],
            )
            self.state = self.PENALTY_ROLLING
            return

        if self.state == self.JACK_READY:
            self._capture_legitimate_state()
            self.jack.launch(
                self.angle,
                self.power,
                self.gameplay["min_launch_speed"],
                self.gameplay["max_launch_speed"],
            )
            self.state = self.JACK_ROLLING
            return

        if self.state != self.READY or self.active_ball is None:
            return
        self._capture_legitimate_state()
        self._launch_coloured_ball(self.active_ball)

    def _pass_remaining_human_balls(self) -> None:
        key = self.match.current_key
        if key is None:
            return
        self.match.pass_remaining_balls(key)
        self.referee_message = (
            f"{self.match.player(key).name}: bocce rimanenti Dead Ball"
        )
        next_key = self.match.choose_next_turn(self.jack.position)
        if next_key is None:
            self._finish_end()
        else:
            self._prepare_coloured_turn()

    def _start_timeout(self, kind: str) -> None:
        key = self.match.current_key
        if key is None:
            return
        self.timeout_owner = key
        if kind == "medical":
            accepted = self.match.request_medical_timeout(key)
        else:
            accepted = self.match.request_technical_timeout(key)

        if not accepted:
            self.referee_message = (
                f"{kind.capitalize()} time out già utilizzato"
            )
            return

        self.timeout_return_state = self.state
        self.timeout_kind = f"{kind} time out"
        self.timeout_remaining = 10 * 60.0
        self.referee_message = (
            f"{self.timeout_kind}: cronometro fermato"
        )
        self.state = self.TIMEOUT

    def _select_boccia_type(self, index: int) -> None:
        if self.state not in (self.READY, self.PENALTY_READY):
            return
        if not (0 <= index < len(BOCCIA_PROFILES)):
            return
        self.selected_boccia_type = BOCCIA_PROFILES[index].key
        key = self.match.current_key
        if key is None:
            return
        if self.state == self.PENALTY_READY:
            self.penalty_ball = self._make_ball(key)
        else:
            self.active_ball = self._make_ball(key)

    def _cycle_boccia_type(self, direction: int) -> None:
        if self.state not in (self.READY, self.PENALTY_READY):
            return
        self.selected_boccia_type = cycle_boccia_profile(
            self.selected_boccia_type,
            direction,
        ).key
        key = self.match.current_key
        if key is None:
            return
        if self.state == self.PENALTY_READY:
            self.penalty_ball = self._make_ball(key)
        else:
            self.active_ball = self._make_ball(key)
