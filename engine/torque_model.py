"""
engine.torque_model  –  CSV-driven torque look-up with fallback.

If the given CSV is missing or malformed we fall back to a simple
"increasing then tapering" default curve so the simulator never crashes.
"""

from pathlib import Path
import csv
from bisect import bisect_right
from typing import List, Tuple

# ---------- a really simple built-in curve (RPM , Torque) ----------
_DEFAULT_CURVE: List[Tuple[float, float]] = [
    (1000, 180), (2000, 230), (3000, 280), (4000, 320),
    (5000, 340), (6000, 330), (7000, 300)
]


class TorqueModel:
    def __init__(self, csv_path: Path | None = None) -> None:
        self.curve: List[Tuple[float, float]] = self._load(csv_path)

    # ───────────────────────── lookup ──
    def torque_at(self, rpm: float) -> float:
        pts = self.curve
        if rpm <= pts[0][0]:
            return pts[0][1]
        if rpm >= pts[-1][0]:
            return pts[-1][1]

        i = bisect_right([p[0] for p in pts], rpm) - 1
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        return y0 + (rpm - x0) * (y1 - y0) / (x1 - x0)

    # ───────────────────────── loading ──
    @staticmethod
    def _load(path: Path | None) -> List[Tuple[float, float]]:
        if path is None or not path.exists():
            # no file – use default
            return _DEFAULT_CURVE

        try:
            with path.open() as fp:
                reader = csv.reader(fp)
                header = next(reader)
                # expect RPM,Torque
                pairs = [(float(rpm), float(tq)) for rpm, tq in reader]
            pairs.sort()
            return pairs
        except Exception as err:
            # malformed CSV – log & fall back
            print(f"[TorqueModel] Warning: failed to read '{path}': {err}. "
                  "Using built-in default curve.")
            return _DEFAULT_CURVE
