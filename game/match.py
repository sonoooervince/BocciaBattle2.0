from __future__ import annotations

import pygame

from game.boccia import Boccia
from game.player import Player
from game.scoring import EndScore, calculate_end_score


class MatchController:
    """Gestisce turni, end e punteggio totale della partita."""

    PLAYER_ORDER = ("red", "blue")

    def __init__(
        self,
        balls_per_player: int,
        red_color: tuple[int, int, int],
        blue_color: tuple[int, int, int],
        max_ends: int = 4,
        tie_tolerance_px: float = 0.5,
        red_name: str = "ROSSO",
        blue_name: str = "BLU",
    ) -> None:
        self.balls_per_player = balls_per_player
        self.red_color = red_color
        self.blue_color = blue_color
        self.max_ends = max(1, max_ends)
        self.tie_tolerance_px = max(0.0, tie_tolerance_px)
        self.red_name = red_name
        self.blue_name = blue_name

        self.total_scores = {"red": 0, "blue": 0}
        self.end_history: list[EndScore] = []
        self.current_end = 1
        self.last_throw_key: str | None = None
        self.last_end_score: EndScore | None = None
        self.match_over = False
        self.next_starting_key = "red"

        self.players: dict[str, Player] = {}
        self.current_key: str | None = None
        self._reset_end_state(self.next_starting_key)

    @property
    def current_player(self) -> Player | None:
        if self.current_key is None:
            return None
        return self.players[self.current_key]

    @property
    def all_balls(self) -> list[Boccia]:
        return [
            ball
            for key in self.PLAYER_ORDER
            for ball in self.players[key].balls
        ]

    @property
    def is_tiebreak(self) -> bool:
        return self.current_end > self.max_ends

    @property
    def winner(self) -> str | None:
        if not self.match_over:
            return None
        if self.total_scores["red"] == self.total_scores["blue"]:
            return None
        return (
            "red"
            if self.total_scores["red"] > self.total_scores["blue"]
            else "blue"
        )

    def player(self, key: str) -> Player:
        return self.players[key]

    def register_throw(self, ball: Boccia) -> None:
        player = self.current_player
        if player is None:
            raise RuntimeError("L'end è già terminato.")
        if ball.owner_key != player.key:
            raise RuntimeError("La boccia non appartiene al giocatore di turno.")

        player.register_throw(ball)
        self.last_throw_key = player.key

    def best_ball(
        self,
        key: str,
        jack_position: pygame.Vector2,
    ) -> Boccia | None:
        balls = self.players[key].balls
        if not balls:
            return None
        return min(
            balls,
            key=lambda ball: ball.position.distance_to(jack_position),
        )

    def best_distance(
        self,
        key: str,
        jack_position: pygame.Vector2,
    ) -> float | None:
        ball = self.best_ball(key, jack_position)
        if ball is None:
            return None
        return ball.position.distance_to(jack_position)

    def leader(self, jack_position: pygame.Vector2) -> str | None:
        red_distance = self.best_distance("red", jack_position)
        blue_distance = self.best_distance("blue", jack_position)

        if red_distance is None and blue_distance is None:
            return None
        if red_distance is None:
            return "blue"
        if blue_distance is None:
            return "red"
        if abs(red_distance - blue_distance) <= self.tie_tolerance_px:
            return "tie"
        return "red" if red_distance < blue_distance else "blue"

    def choose_next_turn(self, jack_position: pygame.Vector2) -> str | None:
        red = self.players["red"]
        blue = self.players["blue"]

        if red.remaining <= 0 and blue.remaining <= 0:
            self.current_key = None
            return None

        # Prima assicuriamo almeno un tiro per parte.
        if not red.balls and red.remaining > 0:
            return self._set_current("red")
        if not blue.balls and blue.remaining > 0:
            return self._set_current("blue")

        # Se una parte ha finito le bocce, l'altra completa l'end.
        if red.remaining <= 0:
            return self._set_current("blue")
        if blue.remaining <= 0:
            return self._set_current("red")

        red_distance = self.best_distance("red", jack_position)
        blue_distance = self.best_distance("blue", jack_position)

        if red_distance is None:
            return self._set_current("red")
        if blue_distance is None:
            return self._set_current("blue")

        if abs(red_distance - blue_distance) <= self.tie_tolerance_px:
            other = "blue" if self.last_throw_key == "red" else "red"
            return self._set_current(other)

        farther = "red" if red_distance > blue_distance else "blue"
        return self._set_current(farther)

    def finish_end(self, jack_position: pygame.Vector2) -> EndScore:
        """Calcola e registra il risultato dell'end appena terminato."""
        score = calculate_end_score(
            self.all_balls,
            jack_position,
            tie_tolerance_px=self.tie_tolerance_px,
        )
        self.last_end_score = score
        self.end_history.append(score)

        if score.winner is not None:
            self.total_scores[score.winner] += score.points
            self.next_starting_key = score.winner
        else:
            self.next_starting_key = (
                "blue" if self.next_starting_key == "red" else "red"
            )

        regulation_finished = self.current_end >= self.max_ends
        totals_tied = self.total_scores["red"] == self.total_scores["blue"]
        self.match_over = regulation_finished and not totals_tied
        self.current_key = None
        return score

    def advance_end(self) -> None:
        if self.match_over:
            raise RuntimeError("La partita è già terminata.")
        if self.last_end_score is None:
            raise RuntimeError("L'end corrente non è ancora stato chiuso.")

        self.current_end += 1
        self.last_end_score = None
        self._reset_end_state(self.next_starting_key)

    def restart_match(self) -> None:
        self.total_scores = {"red": 0, "blue": 0}
        self.end_history.clear()
        self.current_end = 1
        self.last_end_score = None
        self.last_throw_key = None
        self.match_over = False
        self.next_starting_key = "red"
        self._reset_end_state(self.next_starting_key)

    def _reset_end_state(self, starting_key: str) -> None:
        self.players = {
            "red": Player(
                "red",
                self.red_name,
                self.red_color,
                self.balls_per_player,
            ),
            "blue": Player(
                "blue",
                self.blue_name,
                self.blue_color,
                self.balls_per_player,
            ),
        }
        self.current_key = starting_key
        self.last_throw_key = None

    def _set_current(self, key: str) -> str:
        self.current_key = key
        return key
