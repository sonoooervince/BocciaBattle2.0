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
    """IA tattica semplice e fisica: decide il tiro, poi usa il normale motore di gioco."""

    def __init__(
        self,
        min_speed: float,
        max_speed: float,
        friction_deceleration: float,
        difficulty: str = "normal",
        seed: int | None = None,
    ) -> None:
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.friction = max(1.0, friction_deceleration)
        self.difficulty = difficulty
        self.random = random.Random(seed)

    def choose_shot(
        self,
        match: MatchController,
        jack: Jack,
    ) -> ShotPlan:
        own = match.player("blue").balls
        opponent = match.player("red").balls

        own_best = match.best_ball("blue", jack.position)
        opponent_best = match.best_ball("red", jack.position)

        if opponent_best is None:
            decision = "AVVICINAMENTO"
            target = jack.position.copy()
            desired_distance = 18.0
            power = self._power_for_distance(
                match.best_distance("blue", jack.position),
                desired_distance,
            )
        elif own_best is None:
            decision = "AVVICINAMENTO"
            target = jack.position.copy()
            desired_distance = 20.0
            power = self._power_for_distance(None, desired_distance, fallback=42.0)
        else:
            own_distance = own_best.position.distance_to(jack.position)
            opponent_distance = opponent_best.position.distance_to(jack.position)

            # Se l'avversario è nettamente meglio piazzato, proviamo una bocciata.
            if opponent_distance + 45.0 < own_distance:
                decision = "BOCCIATA"
                target = opponent_best.position.copy()
                hit_distance = own_best.position.distance_to(target)
                power = self._power_for_distance(
                    hit_distance,
                    desired_distance=70.0,
                    fallback=62.0,
                )
            # Se siamo già in vantaggio, privilegiamo un avvicinamento controllato.
            elif own_distance + 35.0 < opponent_distance:
                decision = "AVVICINAMENTO"
                target = jack.position.copy()
                desired_distance = 24.0
                power = self._power_for_distance(
                    own_distance,
                    desired_distance,
                    fallback=38.0,
                )
            else:
                # Situazione contesa: tiro sul pallino per provare a modificare la zona.
                decision = "ATTACCO AL JACK"
                target = jack.position.copy()
                desired_distance = 42.0
                power = self._power_for_distance(
                    own_distance,
                    desired_distance,
                    fallback=55.0,
                )

        angle = self._angle_from_target(target, match)
        angle, power = self._apply_error(angle, power)

        return ShotPlan(
            angle=max(-70.0, min(70.0, angle)),
            power=max(10.0, min(100.0, power)),
            decision=decision,
            target=target,
        )

    def _power_for_distance(
        self,
        current_distance: float | None,
        desired_distance: float,
        fallback: float = 50.0,
    ) -> float:
        if current_distance is None:
            return fallback

        # Stima fisica della velocità necessaria: v² = 2*a*s.
        travel = max(70.0, current_distance - desired_distance)
        required_speed = math.sqrt(2.0 * self.friction * travel)
        normalized = (required_speed - self.min_speed) / (
            self.max_speed - self.min_speed
        )
        return max(10.0, min(100.0, normalized * 100.0))

    def _angle_from_target(
        self,
        target: pygame.Vector2,
        match: MatchController,
    ) -> float:
        # Il tiro parte sempre dal launch point; il target è un punto del campo.
        launch = match.player("blue").balls[-1].position if match.player("blue").balls else None
        if launch is None:
            # Il GameScreen usa il launch point; questo valore viene corretto
            # dal caller tramite target geometry quando la boccia viene creata.
            return 0.0
        vector = target - launch
        if vector.length_squared() < 1.0:
            return 0.0
        return math.degrees(math.atan2(vector.x, -vector.y))

    def choose_shot_from_launch(
        self,
        match: MatchController,
        jack: Jack,
        launch_point: pygame.Vector2,
    ) -> ShotPlan:
        plan = self.choose_shot(match, jack)
        vector = plan.target - launch_point
        if vector.length_squared() >= 1.0:
            angle = math.degrees(math.atan2(vector.x, -vector.y))
            angle = max(-70.0, min(70.0, angle))
        else:
            angle = 0.0

        return ShotPlan(
            angle=angle,
            power=plan.power,
            decision=plan.decision,
            target=plan.target,
        )

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
