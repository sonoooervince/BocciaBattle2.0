from dataclasses import dataclass

MIN_HUMAN_PLAYERS = 50

@dataclass(frozen=True)
class MatchmakingDecision:
    human_first: bool
    bot_fallback: bool
    bot_level: int

def choose_matchmaking(online_humans: int, target_bot_level: int = 1) -> MatchmakingDecision:
    return MatchmakingDecision(
        human_first=int(online_humans) >= MIN_HUMAN_PLAYERS,
        bot_fallback=True,
        bot_level=max(1, min(50, int(target_bot_level))),
    )
