import math
import unittest

import pygame

from game.config import load_settings
from game.player_profile import apply_profile_equipment, PlayerProfile
from game.user_settings import apply_user_settings, default_user_settings
from screens.game_screen import GameScreen


class TargetAimGameplayTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        settings = apply_user_settings(
            load_settings(),
            default_user_settings(),
        )
        settings = apply_profile_equipment(settings, PlayerProfile())
        self.surface = pygame.Surface(
            (
                settings["window"]["width"],
                settings["window"]["height"],
            )
        )
        self.game = GameScreen(
            self.surface,
            settings,
            progression_enabled=False,
        )
        self.game.state = self.game.READY
        self.game.match.current_key = self.game.human_key

    def tearDown(self) -> None:
        pygame.quit()

    def test_target_aim_sets_marker_angle_and_power(self) -> None:
        point = (
            int(self.game.field.rect.centerx),
            int(self.game.field.rect.top + 150),
        )
        self.game._aim_at_mouse(point)
        self.assertIsNotNone(self.game.target_marker)
        self.assertTrue(
            self.game.gameplay["min_power"]
            <= self.game.power
            <= self.game.gameplay["max_power"]
        )
        self.assertTrue(math.isfinite(self.game.angle))


if __name__ == "__main__":
    unittest.main()
