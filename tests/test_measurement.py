import unittest

import pygame

from game.boccia import Boccia
from game.measurement import (
    measure_balls,
    needs_precision_measurement,
    pixels_to_cm,
)


class MeasurementTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_full_field_height_converts_to_1250_cm(self) -> None:
        self.assertAlmostEqual(
            pixels_to_cm(750, 750),
            1250.0,
            places=4,
        )

    def test_measurements_are_sorted(self) -> None:
        jack = pygame.Vector2(100, 100)
        far = Boccia(pygame.Vector2(130, 100), 3, (255, 0, 0), "red")
        near = Boccia(pygame.Vector2(106, 100), 3, (0, 0, 255), "blue")
        values = measure_balls([far, near], jack, 750)
        self.assertIs(values[0].ball, near)
        self.assertIs(values[1].ball, far)

    def test_close_balls_trigger_precision_measurement(self) -> None:
        jack = pygame.Vector2(100, 100)
        a = Boccia(pygame.Vector2(106, 100), 3, (255, 0, 0), "red")
        b = Boccia(pygame.Vector2(107, 100), 3, (0, 0, 255), "blue")
        values = measure_balls([a, b], jack, 750)
        self.assertTrue(needs_precision_measurement(values))


if __name__ == "__main__":
    unittest.main()
