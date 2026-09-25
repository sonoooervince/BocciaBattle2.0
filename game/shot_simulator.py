from __future__ import annotations

import copy
from dataclasses import dataclass

import pygame

from game.boccia import Boccia
from game.jack import Jack
from game.physics import PhysicsEngine
from game.scoring import calculate_end_score


@dataclass(frozen=True)
class SimulationResult:
    red_points: int
    blue_points: int
    shot_distance_to_jack: float
    jack_displacement: float
    ball_collisions: int
    jack_hits: int
    shot_out: bool

    def tactical_value(self, side_key: str) -> float:
        own = self.red_points if side_key == "red" else self.blue_points
        opponent = self.blue_points if side_key == "red" else self.red_points

        value = own * 120.0 - opponent * 145.0
        value -= self.shot_distance_to_jack * 0.28
        value += min(70.0, self.ball_collisions * 10.0)
        value += min(50.0, self.jack_hits * 8.0)

        if self.shot_out:
            value -= 240.0
        return value


class ShotSimulator:
    """Small deterministic rollout using the same PhysicsEngine as gameplay."""

    def __init__(
        self,
        physics_settings: dict,
        bounds: pygame.Rect,
        cross_position: pygame.Vector2,
        ball_radius: int,
        ball_mass: float,
        min_speed: float,
        max_speed: float,
    ) -> None:
        self.physics_settings = dict(physics_settings)
        self.bounds = bounds.copy()
        self.cross_position = cross_position.copy()
        self.ball_radius = ball_radius
        self.ball_mass = ball_mass
        self.min_speed = min_speed
        self.max_speed = max_speed

    def simulate(
        self,
        existing_balls: list[Boccia],
        jack: Jack,
        launch_point: pygame.Vector2,
        side_key: str,
        color: tuple[int, int, int],
        boccia_type: str,
        angle: float,
        power: float,
        max_seconds: float = 7.0,
    ) -> SimulationResult:
        balls = [copy.deepcopy(ball) for ball in existing_balls]
        jack_copy = copy.deepcopy(jack)
        initial_jack = jack_copy.position.copy()

        shot = Boccia(
            launch_point,
            radius=self.ball_radius,
            color=color,
            owner_key=side_key,
            mass=self.ball_mass,
            boccia_type=boccia_type,
            rolling_seed=1,
        )
        shot.launch(
            angle,
            power,
            self.min_speed,
            self.max_speed,
        )
        balls.append(shot)

        engine = PhysicsEngine(
            friction_deceleration=self.physics_settings["friction_deceleration"],
            border_restitution=self.physics_settings["border_restitution"],
            border_tangent_damping=self.physics_settings["border_tangent_damping"],
            collision_restitution=self.physics_settings["collision_restitution"],
            stop_speed=self.physics_settings["stop_speed"],
            max_substeps=self.physics_settings["max_substeps"],
            boundary_mode="open",
            solver_iterations=self.physics_settings.get("solver_iterations", 6),
        )

        total_ball_collisions = 0
        total_jack_hits = 0
        shot_out = False
        elapsed = 0.0
        step = 1.0 / 90.0

        while elapsed < max_seconds:
            report = engine.step(
                balls,
                jack_copy,
                step,
                self.bounds,
            )
            total_ball_collisions += report.ball_collisions
            total_jack_hits += report.jack_hits
            elapsed += step

            survivors: list[Boccia] = []
            for ball in balls:
                if self._touches_boundary(ball):
                    if ball is shot:
                        shot_out = True
                    ball.velocity.update(0, 0)
                else:
                    survivors.append(ball)
            balls = survivors

            if self._touches_boundary(jack_copy):
                jack_copy.position = self.cross_position.copy()
                jack_copy.velocity.update(0, 0)

            if engine.is_settled(balls, jack_copy):
                break

        score = calculate_end_score(
            balls,
            jack_copy.position,
            tie_tolerance_px=0.5,
        )
        distance = (
            9999.0
            if shot_out or shot not in balls
            else shot.position.distance_to(jack_copy.position)
        )

        return SimulationResult(
            red_points=score.red_points,
            blue_points=score.blue_points,
            shot_distance_to_jack=distance,
            jack_displacement=initial_jack.distance_to(jack_copy.position),
            ball_collisions=total_ball_collisions,
            jack_hits=total_jack_hits,
            shot_out=shot_out,
        )

    def _touches_boundary(self, body: Boccia | Jack) -> bool:
        x = float(body.position.x)
        y = float(body.position.y)
        radius = float(body.radius)
        return (
            x - radius <= self.bounds.left
            or x + radius >= self.bounds.right
            or y - radius <= self.bounds.top
            or y + radius >= self.bounds.bottom
        )
