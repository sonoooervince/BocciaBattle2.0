from __future__ import annotations

import pygame

from game.boccia import Boccia
from game.official_rules import other_side, scheduled_jack_side
from game.player import Player
from game.scoring import EndScore, calculate_end_score


class MatchController:
    """Rules-aware match state for a two-side World Boccia match."""

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
        seconds_per_side: float = 210.0,
    ) -> None:
        self.balls_per_player = max(1, int(balls_per_player))
        self.red_color = red_color
        self.blue_color = blue_color
        self.max_ends = max(1, int(max_ends))
        self.tie_tolerance_px = max(0.0, tie_tolerance_px)
        self.red_name = red_name
        self.blue_name = blue_name
        self.seconds_per_side = max(1.0, float(seconds_per_side))

        self.total_scores = {"red": 0, "blue": 0}
        self.end_history: list[EndScore] = []
        self.current_end = 1
        self.last_throw_key: str | None = None
        self.last_end_score: EndScore | None = None
        self.match_over = False
        self.needs_tiebreak = False
        self.tiebreak_winner: str | None = None
        self.tiebreak_first_key: str | None = None
        self.tiebreak_count = 0
        self.forfeit_key: str | None = None

        self.players: dict[str, Player] = {}
        self.current_key: str | None = None
        self.jack_valid = False
        self.jack_thrower_key = "red"
        self.opening_side: str | None = None
        self.played_valid = {"red": False, "blue": False}
        self.dead_balls = {"red": 0, "blue": 0}
        self.time_remaining = {
            "red": self.seconds_per_side,
            "blue": self.seconds_per_side,
        }
        self.pending_penalty_balls = {"red": 0, "blue": 0}
        self.scored_penalty_points = {"red": 0, "blue": 0}
        self.yellow_cards = {"red": 0, "blue": 0}
        self.red_cards = {"red": 0, "blue": 0}
        self._equidistant_active = False
        self._equidistant_next_key: str | None = None

        self._reset_regulation_end()

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
        if self.forfeit_key is not None:
            return other_side(self.forfeit_key)
        if self.tiebreak_winner is not None:
            return self.tiebreak_winner
        if self.total_scores["red"] == self.total_scores["blue"]:
            return None
        return (
            "red"
            if self.total_scores["red"] > self.total_scores["blue"]
            else "blue"
        )

    def player(self, key: str) -> Player:
        return self.players[key]

    def begin_jack(self) -> str:
        if self.is_tiebreak:
            raise RuntimeError("Il tie-break usa il Jack sulla croce.")
        self.jack_valid = False
        self.opening_side = None
        self.current_key = self.jack_thrower_key
        return self.jack_thrower_key

    def foul_jack(self) -> str:
        self.jack_thrower_key = other_side(self.jack_thrower_key)
        self.current_key = self.jack_thrower_key
        return self.jack_thrower_key

    def confirm_valid_jack(self) -> None:
        self.jack_valid = True
        self.opening_side = self.jack_thrower_key
        self.current_key = self.jack_thrower_key

    def register_throw(self, ball: Boccia) -> None:
        player = self.current_player
        if player is None:
            raise RuntimeError("Nessun lato è autorizzato a giocare.")
        if ball.owner_key != player.key:
            raise RuntimeError("Boccia giocata dal lato sbagliato.")
        player.register_throw(ball)
        self.last_throw_key = player.key

    def confirm_ball_in_play(self, ball: Boccia) -> None:
        self.played_valid[ball.owner_key] = True

    def mark_ball_dead(self, ball: Boccia) -> None:
        player = self.players[ball.owner_key]
        if ball in player.balls:
            player.balls.remove(ball)
            self.dead_balls[ball.owner_key] += 1

    def pass_remaining_balls(self, key: str) -> int:
        player = self.players[key]
        count = player.remaining
        self.dead_balls[key] += count
        player.remaining = 0
        return count

    def expire_side_time(self, key: str) -> int:
        self.time_remaining[key] = 0.0
        return self.pass_remaining_balls(key)

    def consume_time(self, key: str, seconds: float) -> float:
        self.time_remaining[key] = max(
            0.0,
            self.time_remaining[key] - max(0.0, seconds),
        )
        return self.time_remaining[key]

    def award_penalty_ball(self, to_key: str, count: int = 1) -> None:
        self.pending_penalty_balls[to_key] += max(0, int(count))

    def record_penalty_attempt(self, key: str, scored: bool) -> None:
        if self.pending_penalty_balls[key] <= 0:
            raise RuntimeError("Nessuna penalty ball da giocare.")
        self.pending_penalty_balls[key] -= 1
        if scored:
            self.scored_penalty_points[key] += 1

    def give_yellow_card(self, key: str) -> None:
        self.yellow_cards[key] += 1
        if self.yellow_cards[key] >= 2:
            self.forfeit(key)

    def give_red_card(self, key: str) -> None:
        self.red_cards[key] += 1
        self.forfeit(key)

    def forfeit(self, key: str) -> None:
        self.forfeit_key = key
        self.match_over = True
        self.current_key = None

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
        return (
            None
            if ball is None
            else ball.position.distance_to(jack_position)
        )

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
            red_count, blue_count = self._equidistant_counts(jack_position)
            if red_count == blue_count:
                return "tie"
            return "red" if red_count > blue_count else "blue"
        return "red" if red_distance < blue_distance else "blue"

    def choose_next_turn(self, jack_position: pygame.Vector2) -> str | None:
        red = self.players["red"]
        blue = self.players["blue"]

        if red.remaining <= 0 and blue.remaining <= 0:
            self.current_key = None
            return None

        if self.opening_side is not None:
            opener = self.opening_side
            other = other_side(opener)
            if not self.played_valid[opener] and self.players[opener].remaining > 0:
                return self._set_current(opener)
            if not self.played_valid[other] and self.players[other].remaining > 0:
                return self._set_current(other)

        if red.remaining <= 0:
            return self._set_current("blue")
        if blue.remaining <= 0:
            return self._set_current("red")

        red_distance = self.best_distance("red", jack_position)
        blue_distance = self.best_distance("blue", jack_position)

        if red_distance is None:
            self._reset_equidistant()
            return self._set_current("red")
        if blue_distance is None:
            self._reset_equidistant()
            return self._set_current("blue")

        if abs(red_distance - blue_distance) <= self.tie_tolerance_px:
            red_count, blue_count = self._equidistant_counts(jack_position)
            if red_count != blue_count:
                self._reset_equidistant()
                return self._set_current(
                    "red" if red_count < blue_count else "blue"
                )

            if not self._equidistant_active:
                candidate = self.last_throw_key or "red"
                self._equidistant_active = True
                self._equidistant_next_key = other_side(candidate)
            else:
                candidate = self._equidistant_next_key or "red"
                self._equidistant_next_key = other_side(candidate)

            if self.players[candidate].remaining <= 0:
                candidate = other_side(candidate)
            return self._set_current(candidate)

        self._reset_equidistant()
        farther = "red" if red_distance > blue_distance else "blue"
        return self._set_current(farther)

    def finish_end(self, jack_position: pygame.Vector2) -> EndScore:
        score = calculate_end_score(
            self.all_balls,
            jack_position,
            tie_tolerance_px=self.tie_tolerance_px,
            penalty_points=self.scored_penalty_points,
        )
        self.last_end_score = score
        self.end_history.append(score)
        self.current_key = None

        if self.is_tiebreak:
            if score.red_points != score.blue_points:
                self.tiebreak_winner = score.winner
                self.match_over = True
                self.needs_tiebreak = False
            else:
                self.needs_tiebreak = True
            return score

        self.total_scores["red"] += score.red_points
        self.total_scores["blue"] += score.blue_points

        if self.current_end >= self.max_ends:
            if self.total_scores["red"] == self.total_scores["blue"]:
                self.needs_tiebreak = True
            else:
                self.match_over = True
        return score

    def advance_end(self, first_tiebreak_key: str | None = None) -> None:
        if self.match_over:
            raise RuntimeError("La partita è già terminata.")
        if self.last_end_score is None:
            raise RuntimeError("L'end corrente non è ancora stato chiuso.")

        if self.needs_tiebreak:
            self.tiebreak_count += 1
            if self.tiebreak_first_key is None:
                self.tiebreak_first_key = first_tiebreak_key or "red"
            else:
                self.tiebreak_first_key = other_side(self.tiebreak_first_key)
            self.current_end = self.max_ends + self.tiebreak_count
            self.needs_tiebreak = False
            self.last_end_score = None
            self._reset_end_state(
                self.tiebreak_first_key,
                jack_valid=True,
                opening_side=self.tiebreak_first_key,
            )
            return

        self.current_end += 1
        self.last_end_score = None
        self._reset_regulation_end()

    def restart_match(self) -> None:
        self.total_scores = {"red": 0, "blue": 0}
        self.end_history.clear()
        self.current_end = 1
        self.last_end_score = None
        self.last_throw_key = None
        self.match_over = False
        self.needs_tiebreak = False
        self.tiebreak_winner = None
        self.tiebreak_first_key = None
        self.tiebreak_count = 0
        self.forfeit_key = None
        self._reset_regulation_end()

    def _reset_regulation_end(self) -> None:
        starter = scheduled_jack_side(self.current_end)
        self.jack_thrower_key = starter
        self._reset_end_state(starter, jack_valid=False, opening_side=None)

    def _reset_end_state(
        self,
        starting_key: str,
        jack_valid: bool,
        opening_side: str | None,
    ) -> None:
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
        self.jack_valid = jack_valid
        self.opening_side = opening_side
        self.played_valid = {"red": False, "blue": False}
        self.dead_balls = {"red": 0, "blue": 0}
        self.time_remaining = {
            "red": self.seconds_per_side,
            "blue": self.seconds_per_side,
        }
        self.pending_penalty_balls = {"red": 0, "blue": 0}
        self.scored_penalty_points = {"red": 0, "blue": 0}
        self._reset_equidistant()

    def _equidistant_counts(
        self,
        jack_position: pygame.Vector2,
    ) -> tuple[int, int]:
        red_distances = sorted(
            ball.position.distance_to(jack_position)
            for ball in self.players["red"].balls
        )
        blue_distances = sorted(
            ball.position.distance_to(jack_position)
            for ball in self.players["blue"].balls
        )
        if not red_distances or not blue_distances:
            return (len(red_distances), len(blue_distances))

        closest = min(red_distances[0], blue_distances[0])
        red_count = sum(
            abs(distance - closest) <= self.tie_tolerance_px
            for distance in red_distances
        )
        blue_count = sum(
            abs(distance - closest) <= self.tie_tolerance_px
            for distance in blue_distances
        )
        return red_count, blue_count

    def _reset_equidistant(self) -> None:
        self._equidistant_active = False
        self._equidistant_next_key = None

    def _set_current(self, key: str) -> str:
        self.current_key = key
        return key
