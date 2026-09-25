import unittest

import pygame

from game.boccia import Boccia
from game.field import Field
from game.match import MatchController


class PenaltyBallTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def _match(self) -> MatchController:
        return MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            max_ends=4,
            seconds_per_side=210,
        )

    def test_penalties_alternate_between_sides(self) -> None:
        match = self._match()
        match.award_penalty_ball("red", 2)
        match.award_penalty_ball("blue", 1)
        first = match.begin_penalty_phase(pygame.Vector2(100, 100))
        self.assertEqual(first, "red")
        self.assertEqual(match.penalty_order, ["red", "blue", "red"])

    def test_penalty_point_is_added_after_base_score(self) -> None:
        match = self._match()
        jack = pygame.Vector2(100, 100)
        red = Boccia(pygame.Vector2(90, 100), 5, (255, 0, 0), "red")
        blue = Boccia(pygame.Vector2(140, 100), 5, (0, 0, 255), "blue")
        match.players["red"].balls.append(red)
        match.players["blue"].balls.append(blue)

        match.award_penalty_ball("blue")
        self.assertEqual(match.begin_penalty_phase(jack), "blue")
        match.record_penalty_attempt("blue", scored=True)
        score = match.finish_end(jack)

        self.assertEqual(score.red_points, 1)
        self.assertEqual(score.blue_points, 1)
        self.assertEqual(score.penalty_blue, 1)

    def test_target_box_requires_whole_ball_inside(self) -> None:
        field = Field(pygame.Rect(0, 0, 360, 750))
        ball = Boccia(
            field.cross_position.copy(),
            5,
            (255, 0, 0),
            "red",
        )
        self.assertTrue(field.ball_scores_penalty(ball))
        ball.position.x = field.target_box_rect.left + ball.radius - 0.1
        self.assertFalse(field.ball_scores_penalty(ball))


if __name__ == "__main__":
    unittest.main()
