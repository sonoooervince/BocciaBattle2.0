import unittest

import pygame

from game.boccia import Boccia
from game.field import Field
from game.match import MatchController


class CourtScaleRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_official_ball_scale_can_fit_penalty_box(self) -> None:
        field = Field(pygame.Rect(0, 0, 360, 750))
        ball = Boccia(
            field.cross_position.copy(),
            3,
            (255, 0, 0),
            "red",
        )
        self.assertTrue(field.ball_scores_penalty(ball))

    def test_jack_knocker_plays_when_court_is_empty(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            seconds_per_side=210,
        )
        match.opening_side = "red"
        match.played_valid = {"red": True, "blue": True}
        match.players["red"].remaining = 4
        match.players["blue"].remaining = 4
        next_key = match.choose_next_turn(
            pygame.Vector2(100, 100),
            jack_knocker_if_empty="blue",
        )
        self.assertEqual(next_key, "blue")


if __name__ == "__main__":
    unittest.main()
