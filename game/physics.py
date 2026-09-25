from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import pygame

from game.boccia import Boccia
from game.jack import Jack


@dataclass
class PhysicsReport:
    border_hits: int = 0
    ball_collisions: int = 0
    jack_hits: int = 0


class PhysicsEngine:
    """2D physics with optional open boundaries for official match play."""

    def __init__(
        self,
        friction_deceleration: float,
        border_restitution: float,
        border_tangent_damping: float,
        collision_restitution: float,
        stop_speed: float,
        max_substeps: int,
        boundary_mode: str = "bounce",
    ) -> None:
        self.friction_deceleration = friction_deceleration
        self.border_restitution = border_restitution
        self.border_tangent_damping = border_tangent_damping
        self.collision_restitution = collision_restitution
        self.stop_speed = stop_speed
        self.max_substeps = max(1, max_substeps)
        self.boundary_mode = (
            "open" if boundary_mode == "open" else "bounce"
        )

    def step(
        self,
        balls: Iterable[Boccia],
        jack: Jack,
        dt: float,
        bounds: pygame.Rect,
    ) -> PhysicsReport:
        balls = list(balls)
        bodies = [*balls, jack]
        report = PhysicsReport()
        if not bodies:
            return report

        max_speed = max((body.speed for body in bodies), default=0.0)
        smallest_radius = min((body.radius for body in bodies), default=10)
        safe_distance = max(4.0, smallest_radius * 0.55)
        needed_substeps = max(
            1,
            math.ceil((max_speed * dt) / safe_distance),
        )
        substeps = min(self.max_substeps, needed_substeps)
        sub_dt = dt / substeps

        for _ in range(substeps):
            for body in bodies:
                if self._integrate_body(body, sub_dt, bounds):
                    report.border_hits += 1

            for index, first in enumerate(balls):
                for second in balls[index + 1 :]:
                    if self._resolve_circle_collision(first, second):
                        report.ball_collisions += 1

            for ball in balls:
                if self._resolve_circle_collision(ball, jack):
                    report.jack_hits += 1

        return report

    def is_settled(self, balls: Iterable[Boccia], jack: Jack) -> bool:
        return all(not ball.is_moving for ball in balls) and not jack.is_moving

    def _integrate_body(
        self,
        body: Boccia | Jack,
        dt: float,
        bounds: pygame.Rect,
    ) -> bool:
        if not body.is_moving:
            return False

        body.position += body.velocity * dt
        hit_border = False
        if self.boundary_mode == "bounce":
            hit_border = self._resolve_border_collision(body, bounds)
        self._apply_friction(body, dt)

        if body.speed < self.stop_speed:
            body.velocity.update(0, 0)
        return hit_border

    def _apply_friction(self, body: Boccia | Jack, dt: float) -> None:
        speed = body.speed
        if speed <= 0.0:
            return
        multiplier = getattr(body, "friction_multiplier", 1.0)
        new_speed = max(
            0.0,
            speed - self.friction_deceleration * multiplier * dt,
        )
        if new_speed <= 0.0:
            body.velocity.update(0, 0)
        else:
            body.velocity.scale_to_length(new_speed)

    def _resolve_border_collision(
        self,
        body: Boccia | Jack,
        bounds: pygame.Rect,
    ) -> bool:
        hit = False
        min_x = bounds.left + body.radius
        max_x = bounds.right - body.radius
        min_y = bounds.top + body.radius
        max_y = bounds.bottom - body.radius

        if body.position.x < min_x:
            body.position.x = min_x
            body.velocity.x = abs(body.velocity.x) * self.border_restitution
            body.velocity.y *= self.border_tangent_damping
            hit = True
        elif body.position.x > max_x:
            body.position.x = max_x
            body.velocity.x = -abs(body.velocity.x) * self.border_restitution
            body.velocity.y *= self.border_tangent_damping
            hit = True

        if body.position.y < min_y:
            body.position.y = min_y
            body.velocity.y = abs(body.velocity.y) * self.border_restitution
            body.velocity.x *= self.border_tangent_damping
            hit = True
        elif body.position.y > max_y:
            body.position.y = max_y
            body.velocity.y = -abs(body.velocity.y) * self.border_restitution
            body.velocity.x *= self.border_tangent_damping
            hit = True
        return hit

    def _resolve_circle_collision(
        self,
        first: Boccia | Jack,
        second: Boccia | Jack,
    ) -> bool:
        delta = second.position - first.position
        minimum_distance = first.radius + second.radius
        distance_squared = delta.length_squared()

        if distance_squared >= minimum_distance * minimum_distance:
            return False

        if distance_squared <= 1e-9:
            normal = pygame.Vector2(1.0, 0.0)
            distance = 0.0
        else:
            distance = math.sqrt(distance_squared)
            normal = delta / distance

        inverse_mass_first = 1.0 / first.mass
        inverse_mass_second = 1.0 / second.mass
        inverse_mass_sum = inverse_mass_first + inverse_mass_second

        overlap = minimum_distance - distance
        correction = normal * (overlap / inverse_mass_sum * 0.92)
        first.position -= correction * inverse_mass_first
        second.position += correction * inverse_mass_second

        relative_velocity = second.velocity - first.velocity
        velocity_along_normal = relative_velocity.dot(normal)
        if velocity_along_normal >= 0.0:
            return False

        first_restitution = getattr(
            first,
            "collision_restitution",
            self.collision_restitution,
        )
        second_restitution = getattr(
            second,
            "collision_restitution",
            self.collision_restitution,
        )
        effective_restitution = (
            first_restitution + second_restitution
        ) / 2.0

        impulse_magnitude = (
            -(1.0 + effective_restitution)
            * velocity_along_normal
            / inverse_mass_sum
        )
        impulse = normal * impulse_magnitude
        first.velocity -= impulse * inverse_mass_first
        second.velocity += impulse * inverse_mass_second
        return True
