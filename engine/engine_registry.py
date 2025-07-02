"""
Adds `add_engine()` helper so the UI can create new engine folders at runtime.
"""

from pathlib import Path
import json
import shutil
import re
from typing import Dict, Any

ENGINE_ROOT = Path(__file__).resolve().parent.parent / "assets" / "engines"


def scan_engines() -> Dict[str, Dict[str, Any]]:
    engines: Dict[str, Dict[str, Any]] = {}
    if not ENGINE_ROOT.exists():
        return engines

    for folder in ENGINE_ROOT.iterdir():
        meta_file = folder / "meta.json"
        curve_csv = folder / "torque_curve.csv"
        if folder.is_dir() and meta_file.exists() and curve_csv.exists():
            meta = json.loads(meta_file.read_text())
            meta["folder"] = folder
            meta["curve"]  = curve_csv
            engines[folder.name] = meta
    return engines


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def add_engine(name: str, idle: int, redline: int, csv_src: Path) -> str:
    """
    Create a new engine folder from user inputs.
    Returns the folder key so the UI can refresh.
    """
    ENGINE_ROOT.mkdir(parents=True, exist_ok=True)
    key   = _slugify(name)
    dest  = ENGINE_ROOT / key
    if dest.exists():
        raise FileExistsError(f"Engine '{name}' already exists.")
    dest.mkdir()

    # copy CSV
    csv_dst = dest / "torque_curve.csv"
    shutil.copy(csv_src, csv_dst)

    # meta.json
    meta = {
        "name": name,
        "idle": idle,
        "redline": redline,
        "curve": "torque_curve.csv"
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2))
    return key
