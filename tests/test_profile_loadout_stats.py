import unittest

from game.player_profile import PlayerProfile


class ProfileLoadoutStatsTests(unittest.TestCase):
    def test_primary_and_guest_have_six_slots(self) -> None:
        profile = PlayerProfile()
        profile.normalize_loadouts()
        self.assertEqual(len(profile.ball_loadout), 6)
        self.assertEqual(len(profile.guest_ball_loadout), 6)

    def test_owned_set_can_be_assigned_to_slot(self) -> None:
        profile = PlayerProfile(
            owned_sets=["handi_standard_pro", "apowatec_connect_pro"]
        )
        self.assertTrue(
            profile.set_ball_slot(
                2,
                "apowatec_connect_pro",
                "Soft",
            )
        )
        slot = profile.get_ball_slot(2)
        self.assertEqual(slot["set_id"], "apowatec_connect_pro")
        self.assertEqual(slot["hardness"], "Soft")

    def test_guest_loadout_is_independent(self) -> None:
        profile = PlayerProfile(
            owned_sets=["handi_standard_pro", "apowatec_connect_pro"]
        )
        profile.set_ball_slot(
            0,
            "apowatec_connect_pro",
            "Hard",
            guest=True,
        )
        self.assertNotEqual(
            profile.get_ball_slot(0),
            profile.get_ball_slot(0, guest=True),
        )

    def test_record_shot_updates_precision_and_set_stats(self) -> None:
        profile = PlayerProfile()
        profile.record_shot(
            distance_cm=20,
            hit_ball=True,
            hit_jack=False,
            set_id="handi_standard_pro",
        )
        self.assertEqual(profile.shots, 1)
        self.assertEqual(profile.approaches_25cm, 1)
        self.assertEqual(profile.approaches_50cm, 1)
        self.assertEqual(profile.bocciate_hits, 1)
        self.assertAlmostEqual(profile.average_distance_cm or 0, 20)
        self.assertEqual(
            profile.set_stats["handi_standard_pro"]["shots"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
