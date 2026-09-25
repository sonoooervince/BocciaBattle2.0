import unittest

import pygame

from game.boccia import Boccia
from game.jack import Jack
from game.replay import ReplayRecorder


class ReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_replay_records_multiple_frames(self) -> None:
        ball = Boccia(
            pygame.Vector2(20, 100),
            3,
            (255, 0, 0),
            "red",
        )
        jack = Jack(pygame.Vector2(100, 100), 3)
        recorder = ReplayRecorder(capture_fps=30)

        recorder.start([ball], jack)
        ball.position.x = 40
        recorder.capture([ball], jack, 1 / 30)
        ball.position.x = 60
        recorder.capture([ball], jack, 1 / 30)
        replay = recorder.finish([ball], jack)

        self.assertTrue(replay.available)
        self.assertGreaterEqual(len(replay.frames), 3)
        self.assertNotEqual(
            replay.frames[0].balls[0].x,
            replay.frames[-1].balls[0].x,
        )


if __name__ == "__main__":
    unittest.main()
