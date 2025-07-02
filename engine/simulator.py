from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from engine.torque_model import TorqueModel
from engine.engine_registry import scan_engines


# ───────────────────────────────────────── gearbox helper ──
@dataclass
class Gearbox:
    ratios: Dict[str, float] = None
    order:  Tuple[str, ...]  = ("N", "1", "2", "3", "4", "5", "6")

    def __post_init__(self):
        if self.ratios is None:
            self.ratios = {
                "N": 0.0,
                "1": 3.8, "2": 2.3, "3": 1.52,
                "4": 1.00, "5": 0.80, "6": 0.65,
            }

    def ratio(self, gear: str) -> float:
        return self.ratios.get(gear, 0.0)

    def next_gear(self, cur: str, step: int) -> str:
        try:
            idx = self.order.index(cur)
            idx = max(0, min(len(self.order) - 1, idx + step))
            return self.order[idx]
        except ValueError:
            return "N"


# ───────────────────────────────────────── simulator ──
class EngineSimulator:
    """
    • Throttle has **no effect** in Neutral (N).
    • RPM drops realistically on up-shift (ratio math) & glides to idle on lift.
    • Red-line is enforced (set per-engine).
    """

    def __init__(self) -> None:
        # UI inputs -----------------------------------------------------
        self.throttle = 0.0
        self.timing   = 10.0
        self.boost_cmd= 5.0
        self.afr      = 13.5
        self.gear     = "N"
        self.engine_on= False

        # dynamics ------------------------------------------------------
        self._rpm           = 0.0
        self._rpm_target    = 0.0
        self._boost         = 0.0
        self._gearbox       = Gearbox()

        # engine data ---------------------------------------------------
        self._engines = scan_engines()
        self.load_engine(next(iter(self._engines), None))

    # ───────────────── engine selection ──
    def load_engine(self, key: str | None):
        if key and key in self._engines:
            meta = self._engines[key]
            self.redline  = meta.get("redline", 7500)
            self.idle_rpm = meta.get("idle", 900)
            self._torque_model = TorqueModel(meta["curve"])
        else:
            self.redline  = 7500
            self.idle_rpm = 900
            self._torque_model = TorqueModel(None)

    # ───────────────── main tick ──
    def step(self, dt: float = 0.2) -> Tuple[float, str, float, float]:
        if not self.engine_on:
            self._rpm = 0.0
            return 0.0, "LOW", 0.0, self._rpm

        self._update_rpm(dt)
        self._update_boost(dt)

        hp   = self._calc_power()
        knock= self._calc_knock()
        mpg  = self._calc_mpg()
        return hp, knock, mpg, self._rpm

    # ───────────────── rpm dynamics ──
    def _update_rpm(self, dt: float):
        ratio = self._gearbox.ratio(self.gear)
        thr   = self.throttle / 100.0

        # throttle acceleration ONLY if in gear (ratio>0)
        if thr > 0.01 and ratio > 0:
            accel = 4500 * thr * (ratio / 3.8)      # rpm/s
            self._rpm += accel * dt
        else:
            # coast-down
            decay = 800 if ratio == 0 else 1200     # rpm/s
            self._rpm = max(self._rpm - decay * dt, self.idle_rpm)

        # glide toward shift target
        if self._rpm_target:
            step = 4000 * dt
            delta= self._rpm_target - self._rpm
            if abs(delta) <= step:
                self._rpm = self._rpm_target
                self._rpm_target = 0.0
            else:
                self._rpm += step if delta > 0 else -step

        self._rpm = min(self._rpm, self.redline)

    def _update_boost(self, dt: float):
        lag = 0.5 * (dt / 0.2)
        if self._boost < self.boost_cmd:
            self._boost = min(self.boost_cmd, self._boost + lag)
        elif self._boost > self.boost_cmd:
            self._boost = max(self.boost_cmd, self._boost - lag)

    # ───────────────── power / knock / mpg ──
    def _calc_power(self) -> float:
        # Use *engine* RPM for torque lookup so torque ≠ f(gear)
        engine_rpm = self._rpm
        if engine_rpm <= 0:
            return 0.0

        engine_torque = self._torque_model.torque_at(engine_rpm)
        base_hp       = engine_torque * engine_rpm / 5252.0

        ve         = 1 + self._boost / 14.7
        afr_eff    = 1.05 if 12 <= self.afr <= 13.6 else 0.9
        timing_eff = 1 + (self.timing - 10) / 100
        thr_eff    = self.throttle / 100.0
        return base_hp * ve * afr_eff * timing_eff * thr_eff


    def _calc_knock(self) -> str:
        s = 0
        if self.timing > 20: s += (self.timing - 20)
        if self._boost > 12: s += (self._boost - 12) * 1.5
        if self.afr < 12.5:  s += (12.5 - self.afr) * 3
        return "HIGH" if s > 12 else "MED" if s > 6 else "LOW"

    def _calc_mpg(self) -> float:
        return 40 if self.throttle < 1 else (self.afr/14.7)*(1-self.throttle/100)*40

    # ───────────────── shifts ──
    def upshift(self):   self._shift(+1)
    def downshift(self): self._shift(-1)

    def _shift(self, step: int):
        old = self._gearbox.ratio(self.gear)
        self.gear = self._gearbox.next_gear(self.gear, step)
        new = self._gearbox.ratio(self.gear)
        self._rpm_target = self._rpm * (new/old) if old>0 and new>0 else 0.0
