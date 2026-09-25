from __future__ import annotations

import pygame

from game.boccia import Boccia
from game.player import Player


class MatchController:
    """
    Gestisce i turni della 0.2.

    Regola semplificata:
    - Rosso apre l'end.
    - Blu effettua poi il primo tiro.
    - Da quel momento gioca chi ha la propria boccia migliore più lontana
      dal jack, finché migliora oppure termina le bocce.
    """

    PLAYER_ORDER = ("red", "blue")

    def __init__(
        self,
        balls_per_player: int,
        red_color: tuple[int, int, int],
        blue_color: tuple[int, int, int],
    ) -> None:
        self.balls_per_player = balls_per_player
        self.players = {
            "red": Player("red", "ROSSO", red_color, balls_per_player),
            "blue": Player("blue", "BLU", blue_color, balls_per_player),
        }
        self.current_key: str | None = "red"
        self.last_throw_key: str | None = None
        self.ended = False

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
        return min(balls, key=lambda ball: ball.position.distance_to(jack_position))

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
        if abs(red_distance - blue_distance) < 0.5:
            return "tie"
        return "red" if red_distance < blue_distance else "blue"

    def choose_next_turn(self, jack_position: pygame.Vector2) -> str | None:
        red = self.players["red"]
        blue = self.players["blue"]

        if red.remaining <= 0 and blue.remaining <= 0:
            self.current_key = None
            self.ended = True
            return None

        # Prima assicuriamo almeno un tiro per parte.
        if not red.balls and red.remaining > 0:
            return self._set_current("red")
        if not blue.balls and blue.remaining > 0:
            return self._set_current("blue")

        # Se una parte ha esaurito le bocce, l'altra completa l'end.
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

        # Gioca la parte più lontana dal jack.
        if abs(red_distance - blue_distance) < 0.5:
            other = "blue" if self.last_throw_key == "red" else "red"
            return self._set_current(other)

        farther = "red" if red_distance > blue_distance else "blue"
        return self._set_current(farther)

    def _set_current(self, key: str) -> str:
        self.current_key = key
        return key
