import unittest

from game.user_settings import normalize_user_settings


class AimModeSettingsTests(unittest.TestCase):
    def test_target_is_default(self) -> None:
        self.assertEqual(
            normalize_user_settings({})["aim_mode"],
            "target",
        )

    def test_manual_mode_is_preserved(self) -> None:
        self.assertEqual(
            normalize_user_settings({"aim_mode": "manual"})["aim_mode"],
            "manual",
        )

    def test_invalid_mode_falls_back_to_target(self) -> None:
        self.assertEqual(
            normalize_user_settings({"aim_mode": "invalid"})["aim_mode"],
            "target",
        )


if __name__ == "__main__":
    unittest.main()
