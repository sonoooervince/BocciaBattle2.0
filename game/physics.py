from __future__ import annotations

import pygame

from game.boccia import Boccia


class PhysicsEngine:
    """Fisica base: integrazione, attrito e collisioni con i bordi."""

    def __init__(
        self,
        friction_deceleration: float,
        border_restitution: float,
        border_tangent_damping: float,
        stop_speed: float,
    ) -> None:
        self.friction_deceleration = friction_deceleration
        self.border_restitution = border_restitution
        self.border_tangent_damping = border_tangent_damping
        self.stop_speed = stop_speed

    def step_ball(self, ball: Boccia, dt: float, bounds: pygame.Rect) -> bool:
        """
        Avanza la simulazione di una boccia.

        Restituisce True quando in questo frame avviene un urto col bordo.
        """
        if not ball.is_moving:
            return False

        ball.position += ball.velocity * dt
        hit_border = self._resolve_border_collision(ball, bounds)
        self._apply_friction(ball, dt)

        if ball.speed < self.stop_speed:
            ball.velocity.update(0, 0)

        return hit_border

    def _apply_friction(self, ball: Boccia, dt: float) -> None:
        speed = ball.speed
        if speed <= 0:
            return

        new_speed = max(0.0, speed - self.friction_deceleration * dt)
        if new_speed == 0.0:
            ball.velocity.update(0, 0)
        else:
            ball.velocity.scale_to_length(new_speed)

    def _resolve_border_collision(self, ball: Boccia, bounds: pygame.Rect) -> bool:
        hit = False

        min_x = bounds.left + ball.radius
        max_x = bounds.right - ball.radius
        min_y = bounds.top + ball.radius
        max_y = bounds.bottom - ball.radius

        if ball.position.x < min_x:
            ball.position.x = min_x
            ball.velocity.x = abs(ball.velocity.x) * self.border_restitution
            ball.velocity.y *= self.border_tangent_damping
            hit = True
        elif ball.position.x > max_x:
            ball.position.x = max_x
            ball.velocity.x = -abs(ball.velocity.x) * self.border_restitution
            ball.velocity.y *= self.border_tangent_damping
            hit = True

        if ball.position.y < min_y:
            ball.position.y = min_y
            ball.velocity.y = abs(ball.velocity.y) * self.border_restitution
            ball.velocity.x *= self.border_tangent_damping
            hit = True
        elif ball.position.y > max_y:
            ball.position.y = max_y
            ball.velocity.y = -abs(ball.velocity.y) * self.border_restitution
            ball.velocity.x *= self.border_tangent_damping
            hit = True

        return hit
