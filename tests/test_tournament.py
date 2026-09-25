import unittest

from game.tournament import TournamentSession, WeeklyTournament


class TournamentSessionTests(unittest.TestCase):
    def test_weekly_levels_are_progressive(self) -> None:
        tournament = WeeklyTournament.current()
        self.assertEqual(
            [round_.bot_level for round_ in tournament.rounds],
            [5, 10, 18, 27, 36, 44, 50],
        )

    def test_player_advances_after_win(self) -> None:
        session = TournamentSession()
        result = session.record_match("red")

        self.assertEqual(result.status, "advanced")
        self.assertEqual(result.completed_round, 1)
        self.assertEqual(result.next_round, 2)
        self.assertEqual(session.current_bot_level, 10)

        session.prepare_next_match()
        self.assertIsNone(session.last_progress)

    def test_player_is_eliminated_after_loss(self) -> None:
        session = TournamentSession()
        result = session.record_match("blue")

        self.assertEqual(result.status, "eliminated")
        self.assertTrue(session.finished)
        self.assertTrue(session.eliminated)

    def test_seven_wins_make_champion(self) -> None:
        session = TournamentSession()

        for expected_round in range(1, 8):
            result = session.record_match("red")
            self.assertEqual(result.completed_round, expected_round)
            if expected_round < 7:
                self.assertEqual(result.status, "advanced")
                session.prepare_next_match()

        self.assertEqual(result.status, "champion")
        self.assertTrue(session.finished)
        self.assertTrue(session.champion)


if __name__ == "__main__":
    unittest.main()
