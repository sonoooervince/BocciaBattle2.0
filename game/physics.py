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
    swept_collisions: int = 0


class PhysicsEngine:
    """Rigid-circle physics with iterative contacts and swept-circle CCD."""

    def __init__(
        self,
        friction_deceleration: float,
        border_restitution: float,
        border_tangent_damping: float,
        collision_restitution: float,
        stop_speed: float,
        max_substeps: int,
        boundary_mode: str = "bounce",
        solver_iterations: int = 6,
        continuous_collision_detection: bool = True,
    ) -> None:
        self.friction_deceleration = friction_deceleration
        self.border_restitution = border_restitution
        self.border_tangent_damping = border_tangent_damping
        self.collision_restitution = collision_restitution
        self.stop_speed = stop_speed
        self.max_substeps = max(1, max_substeps)
        self.solver_iterations = max(1, solver_iterations)
        self.continuous_collision_detection = bool(
            continuous_collision_detection
        )
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
        bodies: list[Boccia | Jack] = [*balls, jack]
        report = PhysicsReport()

        max_speed = max((body.speed for body in bodies), default=0.0)
        smallest_radius = min(
            (float(body.radius) for body in bodies),
            default=3.0,
        )

        safe_distance = max(0.75, smallest_radius * 0.45)
        needed_substeps = max(
            1,
            math.ceil((max_speed * max(0.0, dt)) / safe_distance),
        )
        substeps = min(self.max_substeps, needed_substeps)
        sub_dt = dt / substeps if substeps else 0.0

        ball_contacts: set[tuple[int, int]] = set()
        jack_contacts: set[tuple[int, int]] = set()

        for _ in range(substeps):
            previous_positions = {
                id(body): body.position.copy()
                for body in bodies
            }

            for body in bodies:
                if self._integrate_body(body, sub_dt, bounds):
                    report.border_hits += 1

            if self.continuous_collision_detection and sub_dt > 0.0:
                for first_index, first in enumerate(bodies):
                    for second in bodies[first_index + 1 :]:
                        if not self._resolve_swept_collision(
                            first,
                            second,
                            previous_positions[id(first)],
                            previous_positions[id(second)],
                            sub_dt,
                        ):
                            continue

                        report.swept_collisions += 1
                        self._register_contact(
                            first,
                            second,
                            ball_contacts,
                            jack_contacts,
                        )

            # Sequential impulse iterations propagate A -> B -> C chains
            # during the same simulation step.
            for _iteration in range(self.solver_iterations):
                any_contact = False

                for first_index, first in enumerate(bodies):
                    for second in bodies[first_index + 1 :]:
                        if not self._resolve_circle_collision(first, second):
                            continue

                        any_contact = True
                        self._register_contact(
                            first,
                            second,
                            ball_contacts,
                            jack_contacts,
                        )

                if not any_contact:
                    break

        report.ball_collisions = len(ball_contacts)
        report.jack_hits = len(jack_contacts)
        return report

    def is_settled(self, balls: Iterable[Boccia], jack: Jack) -> bool:
        return all(not ball.is_moving for ball in balls) and not jack.is_moving

    @staticmethod
    def _register_contact(
        first: Boccia | Jack,
        second: Boccia | Jack,
        ball_contacts: set[tuple[int, int]],
        jack_contacts: set[tuple[int, int]],
    ) -> None:
        key = tuple(sorted((id(first), id(second))))
        if isinstance(first, Jack) or isinstance(second, Jack):
            jack_contacts.add(key)
        else:
            ball_contacts.add(key)

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

    def _resolve_swept_collision(
        self,
        first: Boccia | Jack,
        second: Boccia | Jack,
        first_start: pygame.Vector2,
        second_start: pygame.Vector2,
        sub_dt: float,
    ) -> bool:
        radius = float(first.radius + second.radius)
        radius_squared = radius * radius

        start_delta = second_start - first_start
        end_delta = second.position - first.position

        # Existing/tangent or currently overlapping contacts are handled by
        # the ordinary iterative solver.
        if start_delta.length_squared() <= radius_squared + 1e-7:
            return False
        if end_delta.length_squared() <= radius_squared + 1e-7:
            return False

        first_move = first.position - first_start
        second_move = second.position - second_start
        relative_move = second_move - first_move

        a = relative_move.length_squared()
        if a <= 1e-12:
            return False

        b = 2.0 * start_delta.dot(relative_move)
        c = start_delta.length_squared() - radius_squared
        discriminant = b * b - 4.0 * a * c

        if discriminant < 0.0:
            return False

        root = math.sqrt(discriminant)
        t1 = (-b - root) / (2.0 * a)
        t2 = (-b + root) / (2.0 * a)

        candidates = [
            value
            for value in (t1, t2)
            if -1e-7 <= value <= 1.0 + 1e-7
        ]
        if not candidates:
            return False

        impact_t = max(0.0, min(1.0, min(candidates)))

        first_impact = first_start + first_move * impact_t
        second_impact = second_start + second_move * impact_t
        impact_delta = second_impact - first_impact

        if impact_delta.length_squared() <= 1e-12:
            return False

        normal = impact_delta.normalize()

        # Only resolve if the bodies are moving toward one another.
        relative_velocity = second.velocity - first.velocity
        if relative_velocity.dot(normal) >= -1e-7:
            return False

        first.position = first_impact
        second.position = second_impact

        if not self._apply_collision_impulse(first, second, normal):
            return False

        remaining_time = sub_dt * (1.0 - impact_t)
        if remaining_time > 0.0:
            first.position += first.velocity * remaining_time
            second.position += second.velocity * remaining_time

        return True

    def _resolve_circle_collision(
        self,
        first: Boccia | Jack,
        second: Boccia | Jack,
    ) -> bool:
        delta = second.position - first.position
        minimum_distance = float(first.radius + second.radius)
        distance_squared = delta.length_squared()

        if distance_squared > minimum_distance * minimum_distance + 1e-7:
            return False

        if distance_squared <= 1e-12:
            relative = first.velocity - second.velocity
            normal = (
                relative.normalize()
                if relative.length_squared() > 1e-12
                else pygame.Vector2(1.0, 0.0)
            )
            distance = 0.0
        else:
            distance = math.sqrt(distance_squared)
            normal = delta / distance

        inverse_mass_first = 1.0 / first.mass
        inverse_mass_second = 1.0 / second.mass
        inverse_mass_sum = inverse_mass_first + inverse_mass_second

        penetration = max(0.0, minimum_distance - distance)
        if penetration > 0.0:
            correction = (
                normal
                * (penetration / inverse_mass_sum)
                * 0.98
            )
            first.position -= correction * inverse_mass_first
            second.position += correction * inverse_mass_second

        self._apply_collision_impulse(first, second, normal)
        return True

    def _apply_collision_impulse(
        self,
        first: Boccia | Jack,
        second: Boccia | Jack,
        normal: pygame.Vector2,
    ) -> bool:
        relative_velocity = second.velocity - first.velocity
        velocity_along_normal = relative_velocity.dot(normal)

        if velocity_along_normal >= -1e-7:
            return False

        inverse_mass_first = 1.0 / first.mass
        inverse_mass_second = 1.0 / second.mass
        inverse_mass_sum = inverse_mass_first + inverse_mass_second

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
        effective_restitution = max(
            0.0,
            min(
                1.0,
                (first_restitution + second_restitution) / 2.0,
            ),
        )

        impulse_magnitude = (
            -(1.0 + effective_restitution)
            * velocity_along_normal
            / inverse_mass_sum
        )
        impulse = normal * impulse_magnitude

        first.velocity -= impulse * inverse_mass_first
        second.velocity += impulse * inverse_mass_second
        return True
