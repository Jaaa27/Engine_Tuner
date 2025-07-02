class EngineSimulator:
    def __init__(self) -> None:
        # ── public / tunable state (UI writes these) ──
        self.throttle   = 70.0      # %
        self.rpm        = 4_000.0   # crank-RPM
        self.timing     = 10.0      # °BTDC
        self.boost_cmd  = 5.0       # desired boost PSI
        self.afr        = 13.5      # Air-Fuel Ratio
        self.gear       = "3"       # current gear

        # ── internal objects & limits ─────────────────
        self._gearbox   = Gearbox() # MUST exist before UI accesses ratios
        self.redline    = 7_500     # RPM soft-limit
        self._boost     = 0.0       # virtual boost with turbo-lag

        # torque-curve loader (safe fallback if CSV missing)
        curve_csv = (Path(__file__).with_suffix('').parent /
                     "curves" / "torque_curve.csv")
        self._torque_model = TorqueModel(curve_csv if curve_csv.exists() else None)
