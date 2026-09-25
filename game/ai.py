from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from game.jack import Jack
from game.match import MatchController
from game.official_rules import other_side
from game.shot_simulator import ShotSimulator


@dataclass(frozen=True)
class ShotPlan:
    angle: float
    power: float
    decision: str
    target: pygame.Vector2
    tactical_score: float = 0.0
    alternatives_checked: int = 1


@dataclass(frozen=True)
class AIProfile:
    level: int
    name: str
    angle_error: float
    power_error: float
    tactical_depth: int
    aggression: float


def get_ai_profile(level: int) -> AIProfile:
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
    t = (level - 1) / 49.0
    return AIProfile(
        level=level,
        name=names[level - 1],
        angle_error=7.0 - 5.7 * t,
        power_error=11.0 - 9.0 * t,
        tactical_depth=1 + min(5, (level - 1) // 10),
        aggression=0.25 + 0.55 * t,
    )


class BocciaAI:
    """AI chooses real angle/power and can evaluate same-physics rollouts."""

    def __init__(
        self,
        min_speed: float,
        max_speed: float,
        friction_deceleration: float,
        difficulty: str = "normal",
        level: int = 10,
        seed: int | None = None,
        simulator: ShotSimulator | None = None,
    ) -> None:
        self.min_speed = min_speed
        self.max_speed = max(min_speed + 1.0, max_speed)
        self.friction = max(1.0, friction_deceleration)
        self.difficulty = difficulty
        self.level = max(1, min(50, int(level)))
        self.profile = get_ai_profile(self.level)
        self.random = random.Random(seed)
        self.simulator = simulator

    def set_level(self, level: int) -> None:
        self.level = max(1, min(50, int(level)))
        self.profile = get_ai_profile(self.level)

    def choose_jack_shot(
        self,
        launch_point: pygame.Vector2,
        target: pygame.Vector2,
    ) -> ShotPlan:
        travel = launch_point.distance_to(target)
        power = self._power_for_travel(travel, stop_margin=-10.0)
        angle = self._angle_from_target(target, launch_point)

        angle += self.random.uniform(
            -self.profile.angle_error * 0.35,
            self.profile.angle_error * 0.35,
        )
        power += self.random.uniform(
            -self.profile.power_error * 0.35,
            self.profile.power_error * 0.35,
        )
        return ShotPlan(
            angle=max(-70.0, min(70.0, angle)),
            power=max(10.0, min(100.0, power)),
            decision="LANCIO DEL JACK",
            target=target.copy(),
        )

    def choose_shot(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
        side_key: str = "blue",
        boccia_type: str = "medie",
    ) -> ShotPlan:
        if self.simulator is None or self.level < 12:
            return self._heuristic_shot(
                match,
                jack,
                launch_point,
                side_key,
            )

        raw_candidates = self._tactical_candidates(
            match,
            jack,
            launch_point,
            side_key,
        )

        # Tactical depth determines how many alternatives are actually tested.
        count = min(
            len(raw_candidates),
            2 + self.profile.tactical_depth * 2,
        )
        candidates = raw_candidates[:count]

        player = match.player(side_key)
        best_plan: ShotPlan | None = None
        best_score = -float("inf")

        for decision, target, margin, bonus in candidates:
            angle = self._angle_from_target(target, launch_point)
            travel = launch_point.distance_to(target)
            power = self._power_for_travel(travel, stop_margin=margin)

            result = self.simulator.simulate(
                existing_balls=match.all_balls,
                jack=jack,
                launch_point=launch_point,
                side_key=side_key,
                color=player.color,
                boccia_type=boccia_type,
                angle=angle,
                power=power,
            )
            score = result.tactical_value(side_key) + bonus

            # Prefer controlled approaches when values are essentially equal.
            if decision.startswith("ACCOSTO"):
                score += max(0.0, 35.0 - result.shot_distance_to_jack * 0.12)

            if score > best_score:
                best_score = score
                best_plan = ShotPlan(
                    angle=angle,
                    power=power,
                    decision=decision,
                    target=target.copy(),
                    tactical_score=score,
                    alternatives_checked=count,
                )

        if best_plan is None:
            return self._heuristic_shot(
                match,
                jack,
                launch_point,
                side_key,
            )

        angle, power = self._apply_error(best_plan.angle, best_plan.power)
        return ShotPlan(
            angle=max(-70.0, min(70.0, angle)),
            power=max(10.0, min(100.0, power)),
            decision=best_plan.decision,
            target=best_plan.target,
            tactical_score=best_plan.tactical_score,
            alternatives_checked=best_plan.alternatives_checked,
        )

    def choose_shot_from_launch(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
        side_key: str = "blue",
        boccia_type: str = "medie",
    ) -> ShotPlan:
        return self.choose_shot(
            match,
            jack,
            launch_point,
            side_key=side_key,
            boccia_type=boccia_type,
        )

    def _heuristic_shot(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
        side_key: str,
    ) -> ShotPlan:
        opponent_key = other_side(side_key)
        own_best = match.best_ball(side_key, jack.position)
        opponent_best = match.best_ball(opponent_key, jack.position)

        if opponent_best is None or own_best is None:
            decision = "ACCOSTO"
            target = self._safe_approach_target(
                launch_point,
                jack.position,
                7.0,
            )
            travel = launch_point.distance_to(target)
            power = self._power_for_travel(travel, stop_margin=10.0)
        else:
            own_distance = own_best.position.distance_to(jack.position)
            opponent_distance = opponent_best.position.distance_to(
                jack.position
            )
            behind = own_distance > opponent_distance
            attack_threshold = 45.0 - self.profile.aggression * 18.0

            if behind and opponent_distance + attack_threshold < own_distance:
                decision = "BOCCIATA"
                target = opponent_best.position.copy()
                travel = launch_point.distance_to(target)
                power = self._power_for_travel(travel, stop_margin=65.0)
            elif own_distance + 35.0 < opponent_distance:
                decision = "ACCOSTO"
                target = self._safe_approach_target(
                    launch_point,
                    jack.position,
                    7.0,
                )
                travel = launch_point.distance_to(target)
                power = self._power_for_travel(travel, stop_margin=10.0)
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

    def _tactical_candidates(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
        side_key: str,
    ) -> list[tuple[str, pygame.Vector2, float, float]]:
        opponent_key = other_side(side_key)
        opponent_best = match.best_ball(opponent_key, jack.position)
        own_best = match.best_ball(side_key, jack.position)

        toward_launch = launch_point - jack.position
        if toward_launch.length_squared() < 1.0:
            toward_launch = pygame.Vector2(0, 1)
        else:
            toward_launch = toward_launch.normalize()

        side = pygame.Vector2(-toward_launch.y, toward_launch.x)

        candidates: list[tuple[str, pygame.Vector2, float, float]] = [
            (
                "ACCOSTO CENTRALE",
                jack.position + toward_launch * 7.0,
                8.0,
                12.0,
            ),
            (
                "ACCOSTO SINISTRA",
                jack.position + toward_launch * 8.0 - side * 8.0,
                10.0,
                8.0,
            ),
            (
                "ACCOSTO DESTRA",
                jack.position + toward_launch * 8.0 + side * 8.0,
                10.0,
                8.0,
            ),
            (
                "GUARDIA",
                jack.position + toward_launch * 24.0,
                4.0,
                2.0,
            ),
            (
                "ATTACCO AL JACK",
                jack.position.copy(),
                72.0,
                self.profile.aggression * 18.0,
            ),
        ]

        if opponent_best is not None:
            candidates.insert(
                0,
                (
                    "BOCCIATA AVVERSARIA",
                    opponent_best.position.copy(),
                    68.0,
                    20.0 + self.profile.aggression * 30.0,
                ),
            )

        if own_best is not None and opponent_best is not None:
            own_distance = own_best.position.distance_to(jack.position)
            opponent_distance = opponent_best.position.distance_to(
                jack.position
            )
            if own_distance < opponent_distance:
                # When already scoring, a protective ball often has more value.
                candidates.insert(
                    1,
                    (
                        "BLOCCO DIFENSIVO",
                        jack.position + toward_launch * 18.0,
                        2.0,
                        24.0,
                    ),
                )

        return candidates

    def _power_for_travel(self, travel: float, stop_margin: float) -> float:
        distance = max(50.0, travel + stop_margin)
        required_speed = math.sqrt(2.0 * self.friction * distance)
        normalized = (required_speed - self.min_speed) / (
            self.max_speed - self.min_speed
        )
        return max(10.0, min(100.0, normalized * 100.0))

    @staticmethod
    def _safe_approach_target(
        launch_point: pygame.Vector2,
        jack_position: pygame.Vector2,
        offset: float,
    ) -> pygame.Vector2:
        direction = launch_point - jack_position
        if direction.length_squared() < 1.0:
            direction = pygame.Vector2(0, 1)
        else:
            direction = direction.normalize()
        return jack_position + direction * offset

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
