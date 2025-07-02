import json
from pathlib import Path
from typing import Dict, Any

PRESET_FOLDER = Path(__file__).resolve().parent.parent / "assets" / "maps"
PRESET_FOLDER.mkdir(parents=True, exist_ok=True)

class ConfigLoader:
    """Static helper to read/write tuning JSON files."""

    @staticmethod
    def save(config: Dict[str, Any], dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w") as fp:
            json.dump(config, fp, indent=2)

    @staticmethod
    def load(src: Path) -> Dict[str, Any]:
        with src.open() as fp:
            return json.load(fp)

    # convenience wrappers for presets
    @staticmethod
    def preset_path(name: str) -> Path:
        return PRESET_FOLDER / f"{name.lower()}.json"
