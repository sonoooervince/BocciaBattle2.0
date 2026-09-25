from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BocciaProfile:
    key: str
    label: str
    friction_multiplier: float
    collision_restitution: float
    rolling_variation: float


BOCCIA_PROFILES: tuple[BocciaProfile, ...] = (
    BocciaProfile("super_morbido", "SUPER MORBIDO", 1.30, 0.62, 0.08),
    BocciaProfile("morbide", "MORBIDE", 1.15, 0.68, 0.06),
    BocciaProfile("medie", "MEDIE", 1.00, 0.76, 0.04),
    BocciaProfile("dura", "DURA", 0.88, 0.84, 0.03),
    BocciaProfile("super_duro", "SUPER DURO", 0.78, 0.90, 0.02),
)


def get_boccia_profile(key: str) -> BocciaProfile:
    normalized = str(key).strip().lower()
    for profile in BOCCIA_PROFILES:
        if profile.key == normalized:
            return profile
    return BOCCIA_PROFILES[2]


def cycle_boccia_profile(current_key: str, direction: int = 1) -> BocciaProfile:
    current = get_boccia_profile(current_key)
    index = next(
        index for index, profile in enumerate(BOCCIA_PROFILES)
        if profile.key == current.key
    )
    index = (index + direction) % len(BOCCIA_PROFILES)
    return BOCCIA_PROFILES[index]
