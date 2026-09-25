from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TournamentRound:
    round_number: int
    bot_level: int


@dataclass(frozen=True)
class TournamentProgress:
    status: str
    completed_round: int
    bot_level: int
    next_round: int | None = None
    next_bot_level: int | None = None


@dataclass(frozen=True)
class WeeklyTournament:
    name: str
    rounds: tuple[TournamentRound, ...]

    @staticmethod
    def current() -> "WeeklyTournament":
        levels = (5, 10, 18, 27, 36, 44, 50)
        rounds = tuple(
            TournamentRound(index + 1, level)
            for index, level in enumerate(levels)
        )
        return WeeklyTournament("TORNEO SETTIMANALE", rounds)

    def bot_level_for_round(self, round_number: int) -> int:
        if not self.rounds:
            return 1
        index = max(0, min(len(self.rounds) - 1, round_number - 1))
        return self.rounds[index].bot_level


class TournamentSession:
    """Progressione locale del Torneo Settimanale."""

    def __init__(self, tournament: WeeklyTournament | None = None) -> None:
        self.tournament = tournament or WeeklyTournament.current()
        self.round_index = 0
        self.finished = False
        self.eliminated = False
        self.champion = False
        self.last_progress: TournamentProgress | None = None

    @property
    def total_rounds(self) -> int:
        return len(self.tournament.rounds)

    @property
    def current_round(self) -> TournamentRound:
        if not self.tournament.rounds:
            return TournamentRound(1, 1)
        index = max(0, min(self.round_index, self.total_rounds - 1))
        return self.tournament.rounds[index]

    @property
    def current_bot_level(self) -> int:
        return self.current_round.bot_level

    def record_match(self, winner_key: str) -> TournamentProgress:
        if self.finished:
            raise RuntimeError("Il torneo è già terminato.")
        if self.last_progress is not None:
            raise RuntimeError("Il risultato del round è già stato registrato.")

        completed = self.current_round

        if winner_key != "red":
            self.finished = True
            self.eliminated = True
            self.last_progress = TournamentProgress(
                status="eliminated",
                completed_round=completed.round_number,
                bot_level=completed.bot_level,
            )
            return self.last_progress

        if self.round_index >= self.total_rounds - 1:
            self.finished = True
            self.champion = True
            self.last_progress = TournamentProgress(
                status="champion",
                completed_round=completed.round_number,
                bot_level=completed.bot_level,
            )
            return self.last_progress

        self.round_index += 1
        following = self.current_round
        self.last_progress = TournamentProgress(
            status="advanced",
            completed_round=completed.round_number,
            bot_level=completed.bot_level,
            next_round=following.round_number,
            next_bot_level=following.bot_level,
        )
        return self.last_progress

    def prepare_next_match(self) -> None:
        if self.finished:
            raise RuntimeError("Il torneo è terminato.")
        if self.last_progress is None or self.last_progress.status != "advanced":
            raise RuntimeError("Non c'è un round successivo pronto.")
        self.last_progress = None

    def restart(self) -> None:
        self.round_index = 0
        self.finished = False
        self.eliminated = False
        self.champion = False
        self.last_progress = None
