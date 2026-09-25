import unittest

import pygame

from game.boccia import Boccia
from game.jack import Jack
from game.physics import PhysicsEngine


class AllBallCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.bounds = pygame.Rect(0, 0, 500, 300)
        self.engine = PhysicsEngine(
            friction_deceleration=0,
            border_restitution=0.5,
            border_tangent_damping=1.0,
            collision_restitution=0.9,
            stop_speed=0,
            max_substeps=32,
            boundary_mode="open",
            solver_iterations=6,
        )

    def tearDown(self) -> None:
        pygame.quit()

    def _ball(self, x: float, owner: str = "red") -> Boccia:
        return Boccia(
            pygame.Vector2(x, 100),
            3,
            (255, 0, 0) if owner == "red" else (0, 0, 255),
            owner,
            boccia_type="super_duro",
            rolling_seed=1,
        )

    def test_same_colour_balls_collide(self) -> None:
        moving = self._ball(50, "red")
        target = self._ball(56, "red")
        moving.velocity.update(200, 0)

        self.engine.step(
            [moving, target],
            Jack(pygame.Vector2(300, 200), 3),
            0.0,
            self.bounds,
        )

        self.assertGreater(target.velocity.x, 0)

    def test_opposite_colour_balls_collide(self) -> None:
        moving = self._ball(50, "red")
        target = self._ball(56, "blue")
        moving.velocity.update(200, 0)

        report = self.engine.step(
            [moving, target],
            Jack(pygame.Vector2(300, 200), 3),
            0.0,
            self.bounds,
        )

        self.assertGreater(target.velocity.x, 0)
        self.assertGreaterEqual(report.ball_collisions, 1)

    def test_chain_collision_reaches_every_ball(self) -> None:
        # Moving striker is intentionally last. With a one-pass solver the
        # impulse would not reach the whole cluster in the same frame.
        first = self._ball(60, "red")
        second = self._ball(66, "blue")
        third = self._ball(72, "red")
        fourth = self._ball(78, "blue")
        striker = self._ball(54, "red")
        striker.velocity.update(240, 0)

        self.engine.step(
            [first, second, third, fourth, striker],
            Jack(pygame.Vector2(300, 200), 3),
            0.0,
            self.bounds,
        )

        self.assertGreater(first.velocity.length(), 0)
        self.assertGreater(second.velocity.length(), 0)
        self.assertGreater(third.velocity.length(), 0)
        self.assertGreater(fourth.velocity.length(), 0)

    def test_ball_collides_with_jack(self) -> None:
        ball = self._ball(50)
        jack = Jack(pygame.Vector2(56, 100), 3, mass=1.0)
        ball.velocity.update(180, 0)

        report = self.engine.step(
            [ball],
            jack,
            0.0,
            self.bounds,
        )

        self.assertGreater(jack.velocity.x, 0)
        self.assertGreaterEqual(report.jack_hits, 1)

    def test_ccd_catches_single_step_tunnelling(self) -> None:
        engine = PhysicsEngine(
            friction_deceleration=0,
            border_restitution=0.5,
            border_tangent_damping=1.0,
            collision_restitution=0.9,
            stop_speed=0,
            max_substeps=1,
            boundary_mode="open",
            solver_iterations=1,
            continuous_collision_detection=True,
        )
        moving = self._ball(30, "red")
        target = self._ball(80, "blue")
        moving.velocity.update(1000, 0)
        jack = Jack(pygame.Vector2(300, 200), 3)

        report = engine.step(
            [moving, target],
            jack,
            0.1,
            self.bounds,
        )

        self.assertGreater(target.velocity.length(), 0)
        self.assertGreaterEqual(report.swept_collisions, 1)

    def test_fast_throw_does_not_tunnel_through_ball(self) -> None:
        moving = self._ball(30, "red")
        target = self._ball(80, "blue")
        moving.velocity.update(900, 0)
        jack = Jack(pygame.Vector2(300, 200), 3)

        for _ in range(3):
            self.engine.step(
                [moving, target],
                jack,
                1 / 30,
                self.bounds,
            )

        self.assertGreater(target.velocity.length(), 0)


if __name__ == "__main__":
    unittest.main()
