from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from game.boccia_profiles import get_boccia_profile
from game.brands import get_brand


ROOT_DIR = Path(__file__).resolve().parent.parent
USER_SETTINGS_PATH = ROOT_DIR / "data" / "user_settings.json"


def default_user_settings() -> dict[str, Any]:
    return {
        "preferred_brand": "handi_life_sport",
        "selected_boccia_type": "medie",
        "ai_level": 10,
        "match_ends": 4,
        "ai_think_time": 0.9,
        "show_distance_guides": True,
    }


def load_user_settings() -> dict[str, Any]:
    defaults = default_user_settings()
    if not USER_SETTINGS_PATH.exists():
        return defaults

    try:
        with USER_SETTINGS_PATH.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError):
        return defaults

    merged = defaults | {
        key: value
        for key, value in loaded.items()
        if key in defaults
    }
    return normalize_user_settings(merged)


def save_user_settings(values: dict[str, Any]) -> None:
    normalized = normalize_user_settings(values)
    USER_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USER_SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, indent=2, ensure_ascii=False)


def normalize_user_settings(values: dict[str, Any]) -> dict[str, Any]:
    defaults = default_user_settings()

    brand = get_brand(values.get("preferred_brand", defaults["preferred_brand"]))
    profile = get_boccia_profile(
        values.get("selected_boccia_type", defaults["selected_boccia_type"])
    )

    return {
        "preferred_brand": brand.key,
        "selected_boccia_type": profile.key,
        "ai_level": max(1, min(50, int(values.get("ai_level", 10)))),
        "match_ends": max(1, min(8, int(values.get("match_ends", 4)))),
        "ai_think_time": max(
            0.2,
            min(2.0, float(values.get("ai_think_time", 0.9))),
        ),
        "show_distance_guides": bool(
            values.get("show_distance_guides", True)
        ),
    }


def apply_user_settings(
    base_settings: dict[str, Any],
    user_values: dict[str, Any],
) -> dict[str, Any]:
    settings = copy.deepcopy(base_settings)
    values = normalize_user_settings(user_values)

    gameplay = settings.setdefault("gameplay", {})
    match = settings.setdefault("match", {})

    gameplay["selected_brand"] = values["preferred_brand"]
    gameplay["selected_boccia_type"] = values["selected_boccia_type"]
    gameplay["ai_level"] = values["ai_level"]
    gameplay["ai_think_time"] = values["ai_think_time"]
    gameplay["show_distance_guides"] = values["show_distance_guides"]
    match["ends"] = values["match_ends"]
    return settings


def runtime_user_settings(settings: dict[str, Any]) -> dict[str, Any]:
    gameplay = settings["gameplay"]
    match = settings["match"]
    return normalize_user_settings(
        {
            "preferred_brand": gameplay.get(
                "selected_brand",
                "handi_life_sport",
            ),
            "selected_boccia_type": gameplay.get(
                "selected_boccia_type",
                "medie",
            ),
            "ai_level": gameplay.get("ai_level", 10),
            "match_ends": match.get("ends", 4),
            "ai_think_time": gameplay.get("ai_think_time", 0.9),
            "show_distance_guides": gameplay.get(
                "show_distance_guides",
                True,
            ),
        }
    )
