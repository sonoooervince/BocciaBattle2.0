import unittest

import pygame

from game.config import load_settings
from game.player_profile import PlayerProfile, apply_profile_equipment
from game.user_settings import apply_user_settings, default_user_settings
from screens.local_game_screen import LocalGameScreen


class LocalGameTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        settings = apply_user_settings(
            load_settings(),
            default_user_settings(),
        )
        settings = apply_profile_equipment(settings, PlayerProfile())
        self.surface = pygame.Surface(
            (settings["window"]["width"], settings["window"]["height"])
        )
        self.game = LocalGameScreen(self.surface, settings)

    def tearDown(self) -> None:
        pygame.quit()

    def test_local_mode_has_no_ai_side(self) -> None:
        self.assertEqual(self.game.ai_key, "__none__")

    def test_coin_winner_can_choose_colour(self) -> None:
        self.game.local_coin_winner = "p1"
        self.game._local_choose_colour("blue")
        self.assertEqual(self.game.player1_key, "blue")
        self.assertEqual(self.game.player2_key, "red")
        self.assertEqual(self.game.match.player("blue").name, "GIOCATORE 1")

    def test_both_colours_are_human_controlled(self) -> None:
        self.game._local_choose_colour("red")
        self.game.state = self.game.READY
        self.game.match.current_key = "blue"
        self.assertTrue(self.game._human_can_aim())


if __name__ == "__main__":
    unittest.main()
