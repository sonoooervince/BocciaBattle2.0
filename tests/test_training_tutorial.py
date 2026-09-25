import unittest

from game.training_drills import TRAINING_DRILLS
from screens.tutorial_screen import STEPS


class TrainingTutorialTests(unittest.TestCase):
    def test_training_has_expected_structured_drills(self) -> None:
        keys = [item.key for item in TRAINING_DRILLS]
        self.assertEqual(
            keys,
            [
                "free",
                "approach25",
                "approach50",
                "hit",
                "cluster",
                "corridor",
                "penalty",
            ],
        )

    def test_tutorial_covers_core_game_concepts(self) -> None:
        titles = " ".join(step.title for step in STEPS)
        self.assertIn("ACCOSTO", titles)
        self.assertIn("BOCCIATA", titles)
        self.assertIn("JACK", titles)
        self.assertIn("PENALTY", titles)
        self.assertIn("PUNTEGGIO", titles)
        self.assertIn("TIE-BREAK", titles)


if __name__ == "__main__":
    unittest.main()
