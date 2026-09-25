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


@dataclass(frozen=True)
class AIProfile:
    level: int
    name: str
    angle_error: float
    power_error: float
    tactical_depth: int
    aggression: float


def get_ai_profile(level: int) -> AIProfile:
    """Restituisce uno dei 50 livelli competitivi del computer.

    La forza cresce tramite precisione + qualità decisionale, non tramite
    vantaggi fisici o teletrasporto delle bocce.
    """
    level = max(1, min(50, int(level)))
    names = (
        "Rookie", "Apprendista", "Principiante", "Regolare", "Promessa",
        "Club", "Solido", "Tecnico", "Tattico", "Competitivo",
        "Challenger", "Specialista", "Agile", "Precisione", "Pressing",
        "Veterano", "Controllore", "Stratega", "Aggressivo", "Avanzato",
        "Elite", "Master", "Maestro", "Top Player", "Contender",
        "Pro", "High Level", "World Class", "Finalista", "Semifinalista",
        "Campione", "Tattico Elite", "Specialista Elite", "Precision Master",
        "Match Player", "Tournament Pro", "Grand Challenger", "Elite Pro",
        "World Challenger", "World Elite", "World Master", "World Contender",
        "World Pro", "World Finalist", "World Champion", "Legend",
        "Grand Master", "Supreme", "Apex", "Boccia Battle Legend",
    )
    # Diminuzione progressiva degli errori: i livelli alti sono difficili
    # perché leggono meglio il campo e sbagliano meno, non perché barano.
    t = (level - 1) / 49.0
    angle_error = 7.0 - 5.7 * t
    power_error = 11.0 - 9.0 * t
    tactical_depth = 1 + min(5, (level - 1) // 10)
    aggression = 0.25 + 0.55 * t
    return AIProfile(
        level=level,
        name=names[level - 1],
        angle_error=angle_error,
        power_error=power_error,
        tactical_depth=tactical_depth,
        aggression=aggression,
    )


class BocciaAI:
    """IA tattica che produce un tiro fisico usando lo stesso motore del player."""

    def __init__(
        self,
        min_speed: float,
        max_speed: float,
        friction_deceleration: float,
        difficulty: str = "normal",
        level: int = 10,
        seed: int | None = None,
    ) -> None:
        self.min_speed = min_speed
        self.max_speed = max(min_speed + 1.0, max_speed)
        self.friction = max(1.0, friction_deceleration)
        self.difficulty = difficulty
        self.level = max(1, min(50, int(level)))
        self.profile = get_ai_profile(self.level)
        self.random = random.Random(seed)

    def set_level(self, level: int) -> None:
        self.level = max(1, min(50, int(level)))
        self.profile = get_ai_profile(self.level)

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

            # Ai livelli alti il computer considera più seriamente la bocciata
            # quando è dietro, ma mantiene comunque una scelta tattica leggibile.
            behind = own_distance > opponent_distance
            attack_threshold = 45.0 - self.profile.aggression * 18.0

            if behind and opponent_distance + attack_threshold < own_distance:
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
        # Compatibilità con le tre vecchie difficoltà.
        if self.difficulty == "easy":
            angle_error = max(self.profile.angle_error, 6.0)
            power_error = max(self.profile.power_error, 9.0)
        elif self.difficulty == "hard":
            angle_error = min(self.profile.angle_error, 1.8)
            power_error = min(self.profile.power_error, 3.0)
        else:
            angle_error = self.profile.angle_error
            power_error = self.profile.power_error

        return (
            angle + self.random.uniform(-angle_error, angle_error),
            power + self.random.uniform(-power_error, power_error),
        )
