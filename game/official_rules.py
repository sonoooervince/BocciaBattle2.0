from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


RULES_VERSION = "World Boccia 2025-2028 v1.2.1"
RULES_UPDATED = "2026-04-23"

COURT_WIDTH_M = 6.0
COURT_LENGTH_M = 12.5
TARGET_BOX_M = 0.35
WARMUP_SECONDS = 120
BETWEEN_ENDS_SECONDS = 60
PENALTY_BALL_SECONDS = 60

BALL_WEIGHT_G = 275
BALL_WEIGHT_TOLERANCE_G = 12
BALL_CIRCUMFERENCE_MM = 270
BALL_CIRCUMFERENCE_TOLERANCE_MM = 8


class SportClass(str, Enum):
    BC1 = "BC1"
    BC2 = "BC2"
    BC3 = "BC3"
    BC4 = "BC4"


class EventType(str, Enum):
    INDIVIDUAL = "individual"
    PAIR_BC3 = "pair_bc3"
    PAIR_BC4 = "pair_bc4"
    TEAM = "team"


@dataclass(frozen=True)
class EventFormat:
    event_type: EventType
    ends: int
    balls_per_side: int
    seconds_per_side: int
    red_boxes: tuple[int, ...]
    blue_boxes: tuple[int, ...]
    jack_box_sequence: tuple[int, ...]


INDIVIDUAL_SECONDS = {
    SportClass.BC1: 4 * 60 + 30,
    SportClass.BC2: 3 * 60 + 30,
    SportClass.BC3: 6 * 60,
    SportClass.BC4: 3 * 60 + 30,
}


def normalize_sport_class(value: str | SportClass) -> SportClass:
    if isinstance(value, SportClass):
        return value
    try:
        return SportClass(str(value).upper())
    except ValueError:
        return SportClass.BC2


def get_event_format(
    event_type: str | EventType = EventType.INDIVIDUAL,
    sport_class: str | SportClass = SportClass.BC2,
) -> EventFormat:
    if isinstance(event_type, EventType):
        event = event_type
    else:
        try:
            event = EventType(str(event_type))
        except ValueError:
            event = EventType.INDIVIDUAL
    sport = normalize_sport_class(sport_class)

    if event == EventType.PAIR_BC3:
        return EventFormat(
            event,
            ends=4,
            balls_per_side=6,
            seconds_per_side=7 * 60,
            red_boxes=(2, 4),
            blue_boxes=(3, 5),
            jack_box_sequence=(2, 3, 4, 5),
        )
    if event == EventType.PAIR_BC4:
        return EventFormat(
            event,
            ends=4,
            balls_per_side=6,
            seconds_per_side=4 * 60,
            red_boxes=(2, 4),
            blue_boxes=(3, 5),
            jack_box_sequence=(2, 3, 4, 5),
        )
    if event == EventType.TEAM:
        return EventFormat(
            event,
            ends=6,
            balls_per_side=6,
            seconds_per_side=5 * 60,
            red_boxes=(1, 3, 5),
            blue_boxes=(2, 4, 6),
            jack_box_sequence=(1, 2, 3, 4, 5, 6),
        )

    return EventFormat(
        EventType.INDIVIDUAL,
        ends=4,
        balls_per_side=6,
        seconds_per_side=INDIVIDUAL_SECONDS[sport],
        red_boxes=(3,),
        blue_boxes=(4,),
        jack_box_sequence=(3, 4, 3, 4),
    )


def scheduled_jack_side(end_number: int) -> str:
    return "red" if int(end_number) % 2 == 1 else "blue"


def other_side(side_key: str) -> str:
    return "blue" if side_key == "red" else "red"


@dataclass(frozen=True)
class RuleSupport:
    section: str
    status: str
    note: str


RULE_SUPPORT: tuple[RuleSupport, ...] = (
    RuleSupport("2 Event types", "encoded", "Individual, Pair BC3/BC4 and Team formats/times/boxes are encoded."),
    RuleSupport("3 Court", "engine", "12.5 x 6 m court, six boxes, V-line, cross and 35 cm target box."),
    RuleSupport("4 Equipment", "validation", "Equipment constraints are stored as official constraints; physical equipment is not simulated."),
    RuleSupport("5 Balls", "validation", "Licensed manufacturer catalogue plus official weight/circumference constants."),
    RuleSupport("6 Warm up", "procedure", "Official 2-minute on-court warm-up duration is encoded."),
    RuleSupport("7 Call room", "procedure", "Administrative competition procedure; no physical call room in local video game."),
    RuleSupport("8 Ball check", "validation", "Pre-match legality requirements are encoded; laboratory/referee tests are not physically measurable."),
    RuleSupport("9 Roles", "procedure", "SA/RO/Coach constraints are represented as rules metadata."),
    RuleSupport("10 Play", "engine", "Jack, order of play, clocks, dead balls, out-of-bounds, equidistance and scoring are enforced."),
    RuleSupport("11 Between ends", "engine", "60-second maximum interval is supported by the match state."),
    RuleSupport("12 Disrupted end", "engine", "The exact digital court state is snapshotted before releases and can be restored without estimation."),
    RuleSupport("13 Tie-break", "engine", "Jack on cross, alternating first side, tie-break score excluded from regulation total."),
    RuleSupport("14 Post-match ball check", "validation", "Administrative post-match validation hook."),
    RuleSupport("15 Communication", "procedure", "No live coach/assistant communication exists in single-player gameplay."),
    RuleSupport("16 Violations", "engine", "Dead/retracted balls, penalty-ball counters, cards and forfeits are represented."),
    RuleSupport("17 Disputes", "procedure", "Referee dispute procedure is not a player-mechanical action in local play."),
    RuleSupport("18 Officials signs", "presentation", "Relevant colour/dead-ball/score states are shown in UI rather than physical gestures."),
    RuleSupport("19 Medical timeout", "engine", "One 10-minute medical timeout per side is playable and pauses the match clock."),
    RuleSupport("20 Technical timeout", "engine", "One 10-minute technical timeout per side is playable and pauses the match clock."),
)
