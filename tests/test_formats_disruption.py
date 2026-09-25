import unittest

import pygame

from game.disrupted_end import (
    capture_disrupted_end,
    restore_disrupted_end,
)
from game.jack import Jack
from game.match import MatchController
from game.official_rules import EventType, SportClass, get_event_format


class FormatAndDisruptionTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_enum_event_formats_do_not_fall_back_to_individual(self) -> None:
        pair = get_event_format(EventType.PAIR_BC3, SportClass.BC3)
        team = get_event_format(EventType.TEAM, SportClass.BC1)
        self.assertEqual(pair.event_type, EventType.PAIR_BC3)
        self.assertEqual(pair.seconds_per_side, 420)
        self.assertEqual(team.event_type, EventType.TEAM)
        self.assertEqual(team.ends, 6)

    def test_disrupted_end_restores_exact_state(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
        )
        jack = Jack(pygame.Vector2(100, 100), 3)
        snapshot = capture_disrupted_end(match, jack)

        jack.position.update(300, 400)
        match.player("red").remaining = 1

        restored_match, restored_jack = restore_disrupted_end(snapshot)
        self.assertEqual(restored_match.player("red").remaining, 6)
        self.assertEqual(restored_jack.position, pygame.Vector2(100, 100))


if __name__ == "__main__":
    unittest.main()
