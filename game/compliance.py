from __future__ import annotations

from dataclasses import dataclass

from game.official_rules import (
    BALL_CIRCUMFERENCE_MM,
    BALL_CIRCUMFERENCE_TOLERANCE_MM,
    BALL_WEIGHT_G,
    BALL_WEIGHT_TOLERANCE_G,
)


ALLOWED_BALL_MATERIALS = {
    "vinyl",
    "polyurethane fabric",
    "leather",
    "synthetic leather",
    "suede",
    "similar low-stretch material",
}


@dataclass(frozen=True)
class BallInspection:
    licensed_manufacturer: bool = True
    licensed_logo_visible: bool = True
    manufacturer_logo_visible: bool = True
    weight_g: float = BALL_WEIGHT_G
    circumference_mm: float = BALL_CIRCUMFERENCE_MM
    approved_colour: bool = True
    spherical: bool = True
    uniform_panels: bool = True
    uniform_material: bool = True
    material: str = "synthetic leather"
    legal_filling: bool = True
    non_conductive: bool = True
    non_metallic: bool = True
    non_magnetic: bool = True
    good_condition: bool = True
    tampered: bool = False
    stickers_or_decals: bool = False
    prohibited_substance: bool = False
    prohibited_abrasion: bool = False
    stitching_legal: bool = True

    @property
    def legal(self) -> bool:
        return all(
            (
                self.licensed_manufacturer,
                self.licensed_logo_visible,
                self.manufacturer_logo_visible,
                abs(self.weight_g - BALL_WEIGHT_G)
                <= BALL_WEIGHT_TOLERANCE_G,
                abs(self.circumference_mm - BALL_CIRCUMFERENCE_MM)
                <= BALL_CIRCUMFERENCE_TOLERANCE_MM,
                self.approved_colour,
                self.spherical,
                self.uniform_panels,
                self.uniform_material,
                self.material in ALLOWED_BALL_MATERIALS,
                self.legal_filling,
                self.non_conductive,
                self.non_metallic,
                self.non_magnetic,
                self.good_condition,
                not self.tampered,
                not self.stickers_or_decals,
                not self.prohibited_substance,
                not self.prohibited_abrasion,
                self.stitching_legal,
            )
        )


@dataclass(frozen=True)
class RampInspection:
    fits_2_5m_by_1m: bool = True
    no_propulsion_device: bool = True
    no_speed_device: bool = True
    no_sighting_device: bool = True
    no_obstruction_after_release: bool = True
    legal_side_rails: bool = True
    approved_sticker: bool = True

    @property
    def legal(self) -> bool:
        return all(
            (
                self.fits_2_5m_by_1m,
                self.no_propulsion_device,
                self.no_speed_device,
                self.no_sighting_device,
                self.no_obstruction_after_release,
                self.legal_side_rails,
                self.approved_sticker,
            )
        )


@dataclass(frozen=True)
class WheelchairInspection:
    sport_class: str = "BC2"
    seat_height_cm: float = 66.0
    approved: bool = True
    prohibited_direction_aid: bool = False

    @property
    def legal(self) -> bool:
        height_ok = (
            self.sport_class.upper() == "BC3"
            or self.seat_height_cm <= 66.0
        )
        return (
            self.approved
            and height_ok
            and not self.prohibited_direction_aid
        )


@dataclass(frozen=True)
class SideBallCheck:
    coloured_balls: tuple[BallInspection, ...]
    jack: BallInspection

    @property
    def legal_coloured_count(self) -> int:
        return sum(ball.legal for ball in self.coloured_balls)

    @property
    def may_start_match(self) -> bool:
        # World Boccia requires at least 3 approved coloured balls.
        return self.legal_coloured_count >= 3 and self.jack.legal


def virtual_match_ball_check() -> SideBallCheck:
    """Virtual equipment uses certified nominal specs by construction."""
    return SideBallCheck(
        coloured_balls=tuple(BallInspection() for _ in range(6)),
        jack=BallInspection(),
    )
