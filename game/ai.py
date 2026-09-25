from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from game.match import MatchController
from game.jack import Jack


@dataclass(frozen=True)
class ShotPlan:
    angle: float
    power: float
    decision: str
    target: pygame.Vector2


class BocciaAI:
    """IA tattica leggera che produce un tiro fisico, non un movimento istantaneo."""

    def __init__(
        self,
        min_speed: float,
        max_speed: float,
        friction_deceleration: float,
        difficulty: str = "normal",
        seed: int | None = None,
    ) -> None:
        self.min_speed = min_speed
        self.max_speed = max(min_speed + 1.0, max_speed)
        self.friction = max(1.0, friction_deceleration)
        self.difficulty = difficulty
        self.random = random.Random(seed)

    def choose_shot(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
    ) -> ShotPlan:
        own_best = match.best_ball("blue", jack.position)
        opponent_best = match.best_ball("red", jack.position)

        if opponent_best is None:
            decision = "AVVICINAMENTO"
            target = jack.position.copy()
            travel = launch_point.distance_to(target)
            power = self._power_for_travel(travel, stop_margin=24.0)
        elif own_best is None:
            decision = "AVVICINAMENTO"
            target = jack.position.copy()
            travel = launch_point.distance_to(target)
            power = self._power_for_travel(travel, stop_margin=28.0)
        else:
            own_distance = own_best.position.distance_to(jack.position)
            opponent_distance = opponent_best.position.distance_to(jack.position)

            if opponent_distance + 45.0 < own_distance:
                decision = "BOCCIATA"
                target = opponent_best.position.copy()
                travel = launch_point.distance_to(target)
                power = self._power_for_travel(travel, stop_margin=65.0)
            elif own_distance + 35.0 < opponent_distance:
                decision = "AVVICINAMENTO"
                target = jack.position.copy()
                travel = launch_point.distance_to(target)
                power = self._power_for_travel(travel, stop_margin=24.0)
            else:
                decision = "ATTACCO AL JACK"
                target = jack.position.copy()
                travel = launch_point.distance_to(target)
                power = self._power_for_travel(travel, stop_margin=75.0)

        angle = self._angle_from_target(target, launch_point)
        angle, power = self._apply_error(angle, power)

        return ShotPlan(
            angle=max(-70.0, min(70.0, angle)),
            power=max(10.0, min(100.0, power)),
            decision=decision,
            target=target,
        )

    def choose_shot_from_launch(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
    ) -> ShotPlan:
        return self.choose_shot(match, jack, launch_point)

    def _power_for_travel(self, travel: float, stop_margin: float) -> float:
        distance = max(50.0, travel + stop_margin)
        required_speed = math.sqrt(2.0 * self.friction * distance)
        normalized = (required_speed - self.min_speed) / (
            self.max_speed - self.min_speed
        )
        return max(10.0, min(100.0, normalized * 100.0))

    @staticmethod
    def _angle_from_target(
        target: pygame.Vector2,
        launch_point: pygame.Vector2,
    ) -> float:
        vector = target - launch_point
        if vector.length_squared() < 1.0:
            return 0.0
        return math.degrees(math.atan2(vector.x, -vector.y))

    def _apply_error(self, angle: float, power: float) -> tuple[float, float]:
        if self.difficulty == "easy":
            angle_error = self.random.uniform(-6.0, 6.0)
            power_error = self.random.uniform(-9.0, 9.0)
        elif self.difficulty == "hard":
            angle_error = self.random.uniform(-1.8, 1.8)
            power_error = self.random.uniform(-3.0, 3.0)
        else:
            angle_error = self.random.uniform(-3.5, 3.5)
            power_error = self.random.uniform(-6.0, 6.0)

        return angle + angle_error, power + power_error
