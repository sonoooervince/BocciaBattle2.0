from __future__ import annotations

import copy
from dataclasses import dataclass

from game.jack import Jack
from game.match import MatchController


@dataclass
class DisruptedEndSnapshot:
    match: MatchController
    jack: Jack


def capture_disrupted_end(
    match: MatchController,
    jack: Jack,
) -> DisruptedEndSnapshot:
    """Capture exact digital positions/state before a release."""
    return DisruptedEndSnapshot(
        match=copy.deepcopy(match),
        jack=copy.deepcopy(jack),
    )


def restore_disrupted_end(
    snapshot: DisruptedEndSnapshot,
) -> tuple[MatchController, Jack]:
    """Restore the last legitimate state after a disrupted end."""
    return (
        copy.deepcopy(snapshot.match),
        copy.deepcopy(snapshot.jack),
    )
