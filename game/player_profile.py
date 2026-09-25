from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from game.store_catalog import get_real_set, approximate_profile_key


ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT_DIR / "data" / "player_profile.json"


RANKS: tuple[tuple[int, str], ...] = (
    (0, "ROOKIE"),
    (500, "CLUB"),
    (1500, "REGIONALE"),
    (3000, "NAZIONALE"),
    (5500, "INTERNAZIONALE"),
    (8500, "ELITE"),
    (12500, "MASTER"),
    (18000, "WORLD CLASS"),
    (26000, "CHAMPION"),
    (38000, "LEGEND"),
)


@dataclass
class PlayerProfile:
    xp: int = 0
    gold: int = 1200
    rating: int = 1000
    wins: int = 0
    losses: int = 0
    streak: int = 0
    owned_sets: list[str] = field(
        default_factory=lambda: ["handi_standard_pro"]
    )
    equipped_set: str = "handi_standard_pro"
    equipped_hardness: str = "Medium"

    @property
    def rank(self) -> str:
        name = RANKS[0][1]
        for threshold, candidate in RANKS:
            if self.xp >= threshold:
                name = candidate
        return name

    @property
    def level(self) -> int:
        return 1 + self.xp // 500

    def owns(self, set_id: str) -> bool:
        return set_id in self.owned_sets

    def can_afford(self, amount: int) -> bool:
        return self.gold >= amount

    def purchase(self, set_id: str, price: int) -> bool:
        if self.owns(set_id):
            return True
        if not self.can_afford(price):
            return False
        self.gold -= max(0, int(price))
        self.owned_sets.append(set_id)
        return True

    def equip(self, set_id: str) -> bool:
        if not self.owns(set_id):
            return False
        item = get_real_set(set_id)
        self.equipped_set = item.key
        if self.equipped_hardness not in item.hardnesses:
            self.equipped_hardness = item.hardnesses[0]
        return True

    def reward_match(self, won: bool) -> tuple[int, int]:
        if won:
            xp_gain = 160
            gold_gain = 200 + min(100, self.streak * 10)
            self.wins += 1
            self.streak += 1
            self.rating = min(3000, self.rating + 18)
        else:
            xp_gain = 65
            gold_gain = 80
            self.losses += 1
            self.streak = 0
            self.rating = max(100, self.rating - 10)

        self.xp += xp_gain
        self.gold += gold_gain
        return xp_gain, gold_gain


def load_profile() -> PlayerProfile:
    profile = PlayerProfile()
    if not PROFILE_PATH.exists():
        return profile
    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return profile

    for key in asdict(profile):
        if key in data:
            setattr(profile, key, data[key])

    if "handi_standard_pro" not in profile.owned_sets:
        profile.owned_sets.insert(0, "handi_standard_pro")
    if profile.equipped_set not in profile.owned_sets:
        profile.equipped_set = profile.owned_sets[0]
    profile.equip(profile.equipped_set)
    return profile


def save_profile(profile: PlayerProfile) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROFILE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(asdict(profile), handle, indent=2, ensure_ascii=False)


def apply_profile_equipment(
    settings: dict[str, Any],
    profile: PlayerProfile,
) -> dict[str, Any]:
    item = get_real_set(profile.equipped_set)
    gameplay = settings.setdefault("gameplay", {})
    gameplay["selected_brand"] = item.brand_key
    gameplay["selected_set_id"] = item.key
    gameplay["selected_set_name"] = item.model
    gameplay["selected_boccia_type"] = approximate_profile_key(
        profile.equipped_hardness
    )
    return settings
