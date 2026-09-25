import unittest

import pygame

from game.boccia import Boccia
from game.field import Field
from game.match import MatchController
from game.official_rules import (
    EventType,
    SportClass,
    get_event_format,
    scheduled_jack_side,
)
from game.scoring import calculate_end_score


class OfficialRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_individual_format(self) -> None:
        fmt = get_event_format(EventType.INDIVIDUAL, SportClass.BC2)
        self.assertEqual(fmt.ends, 4)
        self.assertEqual(fmt.balls_per_side, 6)
        self.assertEqual(fmt.seconds_per_side, 210)
        self.assertEqual(fmt.red_boxes, (3,))
        self.assertEqual(fmt.blue_boxes, (4,))

    def test_individual_class_times(self) -> None:
        self.assertEqual(
            get_event_format("individual", "BC1").seconds_per_side,
            270,
        )
        self.assertEqual(
            get_event_format("individual", "BC3").seconds_per_side,
            360,
        )
        self.assertEqual(
            get_event_format("individual", "BC4").seconds_per_side,
            210,
        )

    def test_jack_starter_alternates_by_end(self) -> None:
        self.assertEqual(scheduled_jack_side(1), "red")
        self.assertEqual(scheduled_jack_side(2), "blue")
        self.assertEqual(scheduled_jack_side(3), "red")
        self.assertEqual(scheduled_jack_side(4), "blue")

    def test_field_has_official_target_box_and_jack_zone(self) -> None:
        field = Field(pygame.Rect(0, 0, 360, 750))
        self.assertAlmostEqual(field.target_box_rect.width, 21, delta=1)
        self.assertAlmostEqual(field.target_box_rect.height, 21, delta=1)

        class Body:
            radius = 4

        jack = Body()
        jack.position = field.cross_position.copy()
        self.assertTrue(field.is_valid_jack_position(jack))

        jack.position = pygame.Vector2(
            field.rect.centerx,
            field.throwing_line_y - 20,
        )
        self.assertFalse(field.is_valid_jack_position(jack))

    def test_equidistant_scoring_can_award_both_sides(self) -> None:
        jack = pygame.Vector2(100, 100)
        red1 = Boccia(pygame.Vector2(90, 100), 5, (255, 0, 0), "red")
        red2 = Boccia(pygame.Vector2(110, 100), 5, (255, 0, 0), "red")
        blue = Boccia(pygame.Vector2(100, 110), 5, (0, 0, 255), "blue")
        score = calculate_end_score(
            [red1, red2, blue],
            jack,
            tie_tolerance_px=0.01,
        )
        self.assertEqual(score.red_points, 2)
        self.assertEqual(score.blue_points, 1)

    def test_tiebreak_does_not_change_regulation_total(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            max_ends=4,
            seconds_per_side=210,
        )
        match.total_scores = {"red": 3, "blue": 3}
        match.current_end = 4
        match.last_end_score = calculate_end_score(
            [],
            pygame.Vector2(0, 0),
        )
        match.needs_tiebreak = True
        match.advance_end(first_tiebreak_key="blue")
        self.assertTrue(match.is_tiebreak)
        self.assertEqual(match.current_key, "blue")
        self.assertTrue(match.jack_valid)
        self.assertEqual(match.total_scores, {"red": 3, "blue": 3})

    def test_timeout_turns_remaining_balls_dead(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            seconds_per_side=210,
        )
        dead = match.expire_side_time("red")
        self.assertEqual(dead, 6)
        self.assertEqual(match.player("red").remaining, 0)
        self.assertEqual(match.dead_balls["red"], 6)


if __name__ == "__main__":
    unittest.main()
