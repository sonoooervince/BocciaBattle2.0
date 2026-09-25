import unittest

from game.compliance import (
    BallInspection,
    RampInspection,
    SideBallCheck,
    WheelchairInspection,
    virtual_match_ball_check,
)
from game.match import MatchController


class ComplianceAndTimeoutTests(unittest.TestCase):
    def test_nominal_virtual_set_passes_ball_check(self) -> None:
        self.assertTrue(virtual_match_ball_check().may_start_match)

    def test_ball_outside_weight_tolerance_fails(self) -> None:
        self.assertFalse(BallInspection(weight_g=288).legal)

    def test_at_least_three_coloured_balls_are_required(self) -> None:
        bad = BallInspection(weight_g=400)
        good = BallInspection()
        check = SideBallCheck(
            coloured_balls=(good, good, bad, bad, bad, bad),
            jack=good,
        )
        self.assertFalse(check.may_start_match)

    def test_ramp_and_wheelchair_limits(self) -> None:
        self.assertTrue(RampInspection().legal)
        self.assertFalse(
            WheelchairInspection(
                sport_class="BC2",
                seat_height_cm=67,
            ).legal
        )
        self.assertTrue(
            WheelchairInspection(
                sport_class="BC3",
                seat_height_cm=80,
            ).legal
        )

    def test_each_timeout_can_only_be_used_once(self) -> None:
        match = MatchController(
            6,
            (255, 0, 0),
            (0, 0, 255),
        )
        self.assertTrue(match.request_medical_timeout("red"))
        self.assertFalse(match.request_medical_timeout("red"))
        self.assertTrue(match.request_technical_timeout("red"))
        self.assertFalse(match.request_technical_timeout("red"))


if __name__ == "__main__":
    unittest.main()
