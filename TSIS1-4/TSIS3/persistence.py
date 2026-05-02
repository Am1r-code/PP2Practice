import json
import os
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"
MAX_ENTRIES      = 10

DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "red",       # red | blue | green | yellow | white
    "difficulty":  "normal",    # easy | normal | hard
    "player_name": "Player",
}

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

def load_leaderboard() -> list:
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_leaderboard(entries: list):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_leaderboard_entry(name: str, score: int, distance: int, coins: int) -> list:
    entries = load_leaderboard()
    entries.append({
        "name":     name,
        "score":    score,
        "distance": distance,
        "coins":    coins,
        "date":     datetime.now().strftime("%Y-%m-%d"),
    })
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_ENTRIES]
    save_leaderboard(entries)
    return entries
