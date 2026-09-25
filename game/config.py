from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT_DIR / "data" / "settings.json"


def load_settings() -> dict[str, Any]:
    """Carica le impostazioni locali del prototipo."""
    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)
