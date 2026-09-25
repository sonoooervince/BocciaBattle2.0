import unittest

import pygame

from game.jack import Jack
from game.match import MatchController
from game.online_protocol import build_snapshot, snapshots_match


class OnlineProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def _match(self) -> MatchController:
        return MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
            seconds_per_side=210,
        )

    def test_same_state_has_same_checksum(self) -> None:
        match = self._match()
        jack = Jack(pygame.Vector2(100, 100), 3)
        a = build_snapshot(match, jack)
        b = build_snapshot(match, jack)
        self.assertTrue(snapshots_match(a, b))

    def test_state_change_changes_checksum(self) -> None:
        match = self._match()
        jack = Jack(pygame.Vector2(100, 100), 3)
        before = build_snapshot(match, jack)
        jack.position.x += 1
        after = build_snapshot(match, jack)
        self.assertNotEqual(before.checksum(), after.checksum())


if __name__ == "__main__":
    unittest.main()
