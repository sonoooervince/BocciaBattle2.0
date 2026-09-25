import math
import unittest

import pygame

from game.ai import BocciaAI
from game.field import Field
from game.jack import Jack
from game.match import MatchController
from game.shot_simulator import ShotSimulator


class TacticalAITests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.field = Field(pygame.Rect(0, 0, 360, 750))
        self.physics = {
            "friction_deceleration": 165,
            "border_restitution": 0.54,
            "border_tangent_damping": 0.88,
            "collision_restitution": 0.76,
            "stop_speed": 12,
            "max_substeps": 16,
            "solver_iterations": 4,
        }

    def tearDown(self) -> None:
        pygame.quit()

    def test_high_level_ai_evaluates_multiple_rollouts(self) -> None:
        match = MatchController(
            6,
            (206, 50, 58),
            (48, 112, 204),
            seconds_per_side=210,
        )
        jack = Jack(self.field.cross_position, 3, 1.0)
        simulator = ShotSimulator(
            self.physics,
            self.field.playable_bounds,
            self.field.cross_position,
            ball_radius=3,
            ball_mass=1.0,
            min_speed=220,
            max_speed=900,
        )
        ai = BocciaAI(
            min_speed=220,
            max_speed=900,
            friction_deceleration=165,
            level=50,
            seed=1,
            simulator=simulator,
        )

        plan = ai.choose_shot(
            match,
            jack,
            self.field.launch_point_for("blue"),
            side_key="blue",
        )

        self.assertGreater(plan.alternatives_checked, 1)
        self.assertTrue(math.isfinite(plan.angle))
        self.assertTrue(math.isfinite(plan.power))
        self.assertGreaterEqual(plan.power, 10)
        self.assertLessEqual(plan.power, 100)


if __name__ == "__main__":
    unittest.main()
