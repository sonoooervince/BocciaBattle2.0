from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from game.jack import Jack
from game.match import MatchController
from game.official_rules import RULES_VERSION


PHYSICS_PROTOCOL_VERSION = "1.0-ccd1"


@dataclass(frozen=True)
class OnlineShotCommand:
    match_id: str
    sequence: int
    side_key: str
    phase: str
    angle: float
    power: float
    set_id: str = ""
    hardness: str = ""

    def to_payload(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class OnlineBallState:
    owner_key: str
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    set_id: str
    hardness: str


@dataclass(frozen=True)
class OnlineMatchSnapshot:
    rules_version: str
    physics_version: str
    current_end: int
    current_key: str | None
    red_score: int
    blue_score: int
    red_remaining: int
    blue_remaining: int
    red_time: float
    blue_time: float
    jack_x: float
    jack_y: float
    jack_vx: float
    jack_vy: float
    balls: tuple[OnlineBallState, ...]

    def payload(self) -> dict:
        value = asdict(self)
        value["balls"] = [asdict(ball) for ball in self.balls]
        return value

    def checksum(self) -> str:
        encoded = json.dumps(
            self.payload(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def build_snapshot(
    match: MatchController,
    jack: Jack,
) -> OnlineMatchSnapshot:
    balls = tuple(
        OnlineBallState(
            owner_key=ball.owner_key,
            x=round(float(ball.position.x), 5),
            y=round(float(ball.position.y), 5),
            vx=round(float(ball.velocity.x), 5),
            vy=round(float(ball.velocity.y), 5),
            radius=int(ball.radius),
            set_id=getattr(ball, "set_id", ""),
            hardness=getattr(ball, "hardness", ""),
        )
        for ball in match.all_balls
    )

    return OnlineMatchSnapshot(
        rules_version=RULES_VERSION,
        physics_version=PHYSICS_PROTOCOL_VERSION,
        current_end=match.current_end,
        current_key=match.current_key,
        red_score=match.total_scores["red"],
        blue_score=match.total_scores["blue"],
        red_remaining=match.player("red").remaining,
        blue_remaining=match.player("blue").remaining,
        red_time=round(match.time_remaining["red"], 3),
        blue_time=round(match.time_remaining["blue"], 3),
        jack_x=round(float(jack.position.x), 5),
        jack_y=round(float(jack.position.y), 5),
        jack_vx=round(float(jack.velocity.x), 5),
        jack_vy=round(float(jack.velocity.y), 5),
        balls=balls,
    )


def snapshots_match(
    local: OnlineMatchSnapshot,
    remote: OnlineMatchSnapshot,
) -> bool:
    return local.checksum() == remote.checksum()
