from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from game.store_catalog import approximate_profile_key, get_real_set


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


def default_loadout() -> list[dict[str, str]]:
    return [
        {"set_id": "handi_standard_pro", "hardness": "Medium"}
        for _ in range(6)
    ]


@dataclass
class PlayerProfile:
    xp: int = 0
    gold: int = 1200
    rating: int = 1000
    wins: int = 0
    losses: int = 0
    streak: int = 0

    shots: int = 0
    approaches_25cm: int = 0
    approaches_50cm: int = 0
    bocciate_hits: int = 0
    jack_hits: int = 0
    total_distance_cm: float = 0.0

    owned_sets: list[str] = field(
        default_factory=lambda: ["handi_standard_pro"]
    )
    equipped_set: str = "handi_standard_pro"
    equipped_hardness: str = "Medium"

    # Six competition balls for the main player and for the local guest.
    ball_loadout: list[dict[str, str]] = field(default_factory=default_loadout)
    guest_ball_loadout: list[dict[str, str]] = field(default_factory=default_loadout)

    # Per-real-set statistics.
    set_stats: dict[str, dict[str, float | int]] = field(default_factory=dict)

    tutorial_completed: bool = False

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

    @property
    def average_distance_cm(self) -> float | None:
        if self.shots <= 0:
            return None
        return self.total_distance_cm / self.shots

    @property
    def approach_25_rate(self) -> float:
        return 0.0 if self.shots <= 0 else self.approaches_25cm / self.shots

    @property
    def approach_50_rate(self) -> float:
        return 0.0 if self.shots <= 0 else self.approaches_50cm / self.shots

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

    def normalize_loadouts(self) -> None:
        self.ball_loadout = self._normalize_loadout(self.ball_loadout)
        self.guest_ball_loadout = self._normalize_loadout(
            self.guest_ball_loadout
        )

    def get_ball_slot(
        self,
        slot_index: int,
        guest: bool = False,
    ) -> dict[str, str]:
        self.normalize_loadouts()
        loadout = (
            self.guest_ball_loadout if guest else self.ball_loadout
        )
        index = max(0, min(5, int(slot_index)))
        return dict(loadout[index])

    def set_ball_slot(
        self,
        slot_index: int,
        set_id: str,
        hardness: str,
        guest: bool = False,
    ) -> bool:
        if not self.owns(set_id):
            return False

        item = get_real_set(set_id)
        if hardness not in item.hardnesses:
            hardness = item.hardnesses[0]

        self.normalize_loadouts()
        loadout = (
            self.guest_ball_loadout if guest else self.ball_loadout
        )
        index = max(0, min(5, int(slot_index)))
        loadout[index] = {
            "set_id": item.key,
            "hardness": hardness,
        }
        return True

    def reward_match(
        self,
        won: bool,
        set_id: str | None = None,
    ) -> tuple[int, int]:
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

        if set_id:
            stats = self._set_stats(set_id)
            stats["matches"] = int(stats.get("matches", 0)) + 1
            if won:
                stats["wins"] = int(stats.get("wins", 0)) + 1

        return xp_gain, gold_gain

    def record_shot(
        self,
        distance_cm: float | None,
        hit_ball: bool,
        hit_jack: bool,
        set_id: str,
    ) -> None:
        self.shots += 1

        if distance_cm is not None:
            distance = max(0.0, float(distance_cm))
            self.total_distance_cm += distance
            if distance <= 50.0:
                self.approaches_50cm += 1
            if distance <= 25.0:
                self.approaches_25cm += 1

        if hit_ball:
            self.bocciate_hits += 1
        if hit_jack:
            self.jack_hits += 1

        stats = self._set_stats(set_id)
        stats["shots"] = int(stats.get("shots", 0)) + 1
        stats["ball_hits"] = int(stats.get("ball_hits", 0)) + int(hit_ball)
        stats["jack_hits"] = int(stats.get("jack_hits", 0)) + int(hit_jack)

        if distance_cm is not None:
            stats["distance_sum_cm"] = float(
                stats.get("distance_sum_cm", 0.0)
            ) + max(0.0, float(distance_cm))

    def mark_tutorial_complete(self) -> None:
        self.tutorial_completed = True

    def _normalize_loadout(
        self,
        loadout: list[dict[str, str]] | object,
    ) -> list[dict[str, str]]:
        values = loadout if isinstance(loadout, list) else []
        normalized: list[dict[str, str]] = []

        for index in range(6):
            raw = values[index] if index < len(values) else {}
            if not isinstance(raw, dict):
                raw = {}

            set_id = str(raw.get("set_id", "handi_standard_pro"))
            if not self.owns(set_id):
                set_id = "handi_standard_pro"

            item = get_real_set(set_id)
            hardness = str(raw.get("hardness", item.hardnesses[0]))
            if hardness not in item.hardnesses:
                hardness = item.hardnesses[0]

            normalized.append(
                {
                    "set_id": item.key,
                    "hardness": hardness,
                }
            )

        return normalized

    def _set_stats(self, set_id: str) -> dict[str, float | int]:
        stats = self.set_stats.setdefault(
            set_id,
            {
                "matches": 0,
                "wins": 0,
                "shots": 0,
                "ball_hits": 0,
                "jack_hits": 0,
                "distance_sum_cm": 0.0,
            },
        )
        return stats


def load_profile() -> PlayerProfile:
    profile = PlayerProfile()
    if not PROFILE_PATH.exists():
        profile.normalize_loadouts()
        return profile

    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        profile.normalize_loadouts()
        return profile

    for key in asdict(profile):
        if key in data:
            setattr(profile, key, data[key])

    if "handi_standard_pro" not in profile.owned_sets:
        profile.owned_sets.insert(0, "handi_standard_pro")

    if profile.equipped_set not in profile.owned_sets:
        profile.equipped_set = profile.owned_sets[0]

    profile.equip(profile.equipped_set)
    profile.normalize_loadouts()
    return profile


def save_profile(profile: PlayerProfile) -> None:
    profile.normalize_loadouts()
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
