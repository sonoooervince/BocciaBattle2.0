import unittest

from game.brands import BOCCIA_BRANDS, get_brand
from game.user_settings import normalize_user_settings


class SettingsTests(unittest.TestCase):
    def test_world_boccia_brand_catalog_has_nine_suppliers(self) -> None:
        self.assertEqual(len(BOCCIA_BRANDS), 9)
        self.assertEqual(
            get_brand("handi_life_sport").display_name,
            "Handi Life Sport",
        )

    def test_user_settings_are_clamped(self) -> None:
        values = normalize_user_settings(
            {
                "preferred_brand": "apowatec",
                "selected_boccia_type": "dura",
                "ai_level": 999,
                "sport_class": "BC3",
                "ai_think_time": 8,
                "show_distance_guides": False,
            }
        )
        self.assertEqual(values["ai_level"], 50)
        self.assertEqual(values["sport_class"], "BC3")
        self.assertEqual(values["ai_think_time"], 2.0)
        self.assertFalse(values["show_distance_guides"])


if __name__ == "__main__":
    unittest.main()
