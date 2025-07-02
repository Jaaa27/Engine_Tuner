from pathlib import Path
import json
from typing import Dict, Any

ENGINE_ROOT = Path(__file__).resolve().parent.parent / "assets" / "engines"


def scan_engines() -> Dict[str, Dict[str, Any]]:
    """
    Scan ENGINE_ROOT for folders containing meta.json + torque_curve.csv.
    Returns {key: meta_dict}.  meta["display"] = nice name for UI.
    """
    engines: Dict[str, Dict[str, Any]] = {}
    if not ENGINE_ROOT.exists():
        print("[engine_registry] directory missing:", ENGINE_ROOT)
        return engines

    for folder in ENGINE_ROOT.iterdir():
        if not folder.is_dir():
            continue
        meta_file = folder / "meta.json"
        curve_csv = folder / "torque_curve.csv"
        if meta_file.exists() and curve_csv.exists():
            try:
                meta = json.loads(meta_file.read_text())
                meta["folder"]  = folder
                meta["curve"]   = curve_csv
                meta["display"] = meta.get("name", folder.name)
                meta["idle"]    = meta.get("idle", 900)   # default idle
                engines[folder.name] = meta
                print(f"[engine_registry] + {folder.name} ({meta['display']})")
            except json.JSONDecodeError as err:
                print(f"[engine_registry] ! bad JSON in {meta_file}: {err}")
    if not engines:
        print("[engine_registry] ⚠ no engines found; using fallback curve.")
    return engines
