from dataclasses import dataclass

@dataclass(frozen=True)
class TournamentRound:
    round_number: int
    bot_level: int

@dataclass(frozen=True)
class WeeklyTournament:
    name: str
    rounds: tuple[TournamentRound, ...]

    @staticmethod
    def current() -> "WeeklyTournament":
        levels = (5, 10, 18, 27, 36, 44, 50)
        return WeeklyTournament("TORNEO SETTIMANALE", tuple(TournamentRound(i + 1, level) for i, level in enumerate(levels)))

    def bot_level_for_round(self, round_number: int) -> int:
        if not self.rounds:
            return 1
        return self.rounds[max(0, min(len(self.rounds) - 1, round_number - 1))].bot_level
