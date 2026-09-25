import unittest

import pygame

from game.boccia import Boccia
from game.field import Field
from game.match import MatchController
from game.physics import PhysicsEngine


class GameplayRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.field = Field(pygame.Rect(0, 0, 360, 750))

    def tearDown(self) -> None:
        pygame.quit()

    def test_official_match_uses_six_balls(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            max_ends=4,
            seconds_per_side=210,
        )
        self.assertEqual(match.player("red").remaining, 6)
        self.assertEqual(match.player("blue").remaining, 6)

    def test_open_boundaries_do_not_bounce(self) -> None:
        engine = PhysicsEngine(
            friction_deceleration=0,
            border_restitution=0.5,
            border_tangent_damping=1,
            collision_restitution=0.7,
            stop_speed=0,
            max_substeps=4,
            boundary_mode="open",
        )
        ball = Boccia(
            pygame.Vector2(10, 100),
            5,
            (255, 0, 0),
            "red",
        )
        ball.velocity.update(-100, 0)
        from game.jack import Jack
        jack = Jack(pygame.Vector2(180, 300), 5)
        engine.step([ball], jack, 0.1, self.field.rect)
        self.assertLess(ball.position.x, 10)

    def test_ball_touching_exterior_is_out(self) -> None:
        ball = Boccia(
            pygame.Vector2(5, 100),
            5,
            (255, 0, 0),
            "red",
        )
        self.assertTrue(self.field.touches_exterior_boundary(ball))

    def test_jack_on_cross_is_valid(self) -> None:
        from game.jack import Jack
        jack = Jack(self.field.cross_position, 5)
        jack.has_entered_playing_area = True
        self.assertTrue(self.field.is_valid_jack_position(jack))


if __name__ == "__main__":
    unittest.main()
