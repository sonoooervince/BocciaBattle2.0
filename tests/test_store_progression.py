import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game.player_profile import PlayerProfile
from game.store_catalog import REAL_BOCCIA_SETS, get_real_set


class StoreAndProgressionTests(unittest.TestCase):
    def test_store_contains_only_verified_real_sets(self) -> None:
        self.assertGreaterEqual(len(REAL_BOCCIA_SETS), 20)
        self.assertTrue(
            all(item.verified_real_product for item in REAL_BOCCIA_SETS)
        )
        self.assertTrue(
            all(item.brand_name and item.model for item in REAL_BOCCIA_SETS)
        )

    def test_default_set_is_real_handilife_standard_pro(self) -> None:
        profile = PlayerProfile()
        item = get_real_set(profile.equipped_set)
        self.assertEqual(item.model, "Boccia Standard Pro")
        self.assertEqual(item.gold_cost, 0)

    def test_purchase_and_equip(self) -> None:
        profile = PlayerProfile(gold=5000)
        target = get_real_set("apowatec_connect_pro")
        self.assertTrue(profile.purchase(target.key, target.gold_cost))
        self.assertTrue(profile.equip(target.key))
        self.assertEqual(profile.equipped_set, target.key)
        self.assertLess(profile.gold, 5000)

    def test_match_rewards_give_xp_and_gold(self) -> None:
        profile = PlayerProfile(gold=0)
        xp, gold = profile.reward_match(True)
        self.assertGreater(xp, 0)
        self.assertGreater(gold, 0)
        self.assertEqual(profile.wins, 1)
        self.assertGreater(profile.xp, 0)
        self.assertGreater(profile.gold, 0)


if __name__ == "__main__":
    unittest.main()
