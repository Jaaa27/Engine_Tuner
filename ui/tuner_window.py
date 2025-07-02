import csv, time, tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from engine.simulator import EngineSimulator
from engine.engine_registry import scan_engines


class TunerWindow(tk.Frame):
    """UI with red-line RPM bar & number, numeric HP, smooth graph."""

    # ─────────────────────────── init ────────────────────────────
    def __init__(self, master: tk.Tk):
        super().__init__(master); self.pack(fill="both", expand=True)

        self.sim = EngineSimulator()

        # engine list
        self.engines = scan_engines()
        self.disp_to_key = {m["display"]: k for k, m in self.engines.items()}
        disp_opts = list(self.disp_to_key) or ["default"]
        self.engine_var = tk.StringVar(value=disp_opts[0])

        # recording buffers
        self.recording = False
        self.t = 0.0
        self.ts, self.hp_hist, self.rpm_hist = [], [], []

        # ttk styles for RPM bar
        self._init_styles()

        # build UI
        self._build_ui(disp_opts)
        self._loop()

    # ─────────────────── styles ───────────────────
    def _init_styles(self):
        style = ttk.Style()
        style.configure("RPMGreen.Horizontal.TProgressbar",
                        troughcolor="#dddddd", background="limegreen")
        style.configure("RPMRed.Horizontal.TProgressbar",
                        troughcolor="#dddddd", background="red")

    # ─────────────────── layout ───────────────────
    def _slider(self, label, frm, to, init, res=1):
        s = tk.Scale(self, from_=frm, to=to, resolution=res,
                     orient="horizontal", label=label)
        s.set(init); s.pack(fill="x", padx=8); return s

    def _build_ui(self, disp_opts):
        # sliders
        self.throttle = self._slider("Throttle (%)", 0, 100, 0)
        self.timing   = self._slider("Timing (°BTDC)", 0, 30, 10)
        self.afr      = self._slider("AFR", 10, 16, 13.5, 0.1)
        self.boost    = self._slider("Boost (PSI)", 0, 20, 5)

        # gear row
        g_row = tk.Frame(self); g_row.pack(pady=6)
        tk.Button(g_row, text="▼", width=4, command=self._downshift).pack(side="left")
        self.gear_lbl = tk.Label(g_row, text="Gear: N",
                                 font=("Helvetica", 16, "bold"), width=9)
        self.gear_lbl.pack(side="left", padx=6)
        tk.Button(g_row, text="▲", width=4, command=self._upshift).pack(side="left")

        # engine selector
        e_row = tk.Frame(self); e_row.pack(pady=4)
        tk.Label(e_row, text="Engine:").pack(side="left")
        tk.OptionMenu(e_row, self.engine_var, *disp_opts,
                      command=self._change_engine).pack(side="left")

        # start / stop
        self.start_btn = tk.Button(self, text="Start Engine",
                                   width=15, command=self._toggle_engine)
        self.start_btn.pack(pady=6)

        # recording buttons
        r_row = tk.Frame(self); r_row.pack(pady=4)
        tk.Button(r_row, text="Start Rec", width=12,
                  command=self._start_rec).pack(side="left", padx=4)
        tk.Button(r_row, text="Stop / Export", width=12,
                  command=self._stop_rec).pack(side="left")

        # gauges & graph
        self._add_gauges()
        self._add_graph()

    # ───────────── gauges ─────────────
    def _add_gauges(self):
        g = tk.Frame(self); g.pack(pady=10)

        # RPM bar & number
        tk.Label(g, text="RPM").pack(anchor="w")
        self.rpm_bar = ttk.Progressbar(
            g, orient="horizontal", length=500, mode="determinate",
            maximum=self.sim.redline, style="RPMGreen.Horizontal.TProgressbar"
        )
        self.rpm_bar.pack(pady=2)
        self.rpm_num = tk.Label(g, text="0", font=("Helvetica", 14, "bold"),
                                fg="black")
        self.rpm_num.pack(anchor="e", pady=2)

        # HP numeric
        self.hp_num = tk.Label(g, text="HP: --", font=("Helvetica", 14, "bold"))
        self.hp_num.pack(anchor="w", pady=4)

        # knock / mpg
        self.kn_lbl  = tk.Label(g, text="Knock: --", font=("Helvetica", 12))
        self.mpg_lbl = tk.Label(g, text="Fuel Eff: -- MPG",
                                font=("Helvetica", 12))
        self.kn_lbl.pack(anchor="w"); self.mpg_lbl.pack(anchor="w")

    # ───────────── graph ─────────────
    def _add_graph(self):
        fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)"); self.ax.set_ylabel("HP")
        self.ax.set_title("Recorded Power"); self.ax.grid(True)
        (self.line,) = self.ax.plot([], [], lw=2)
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(pady=6)

    # ───────────── main loop ─────────────
    def _loop(self):
        self.sim.throttle  = self.throttle.get()
        self.sim.timing    = self.timing.get()
        self.sim.afr       = self.afr.get()
        self.sim.boost_cmd = self.boost.get()

        hp, knock, mpg, rpm = self.sim.step(0.2)
        self._update_gauges(hp, rpm)

        if self.recording:
            self.ts.append(self.t); self.hp_hist.append(hp)
            self.rpm_hist.append(rpm); self._update_graph()

        self.kn_lbl.config(text=f"Knock: {knock}")
        self.mpg_lbl.config(text=f"Fuel Eff: {mpg:.1f} MPG")
        self.gear_lbl.config(text=f"Gear: {self.sim.gear}")

        self.t += 0.2
        self.after(200, self._loop)

    # ───────────── gauge update ─────────────
    def _update_gauges(self, hp, rpm):
        # RPM colour logic
        danger = rpm >= 0.95 * self.sim.redline
        style = "RPMRed.Horizontal.TProgressbar" if danger else "RPMGreen.Horizontal.TProgressbar"
        self.rpm_bar.configure(style=style, maximum=self.sim.redline, value=rpm)
        self.rpm_num.config(text=f"{rpm:.0f}", fg=("red" if danger else "black"))

        # HP numeric
        self.hp_num.config(text=f"HP: {hp:.1f}")

    def _update_graph(self):
        self.line.set_data(self.ts, self.hp_hist)
        self.ax.relim(); self.ax.autoscale_view()
        self.canvas.draw_idle()

    # ───────────── controls ─────────────
    def _toggle_engine(self):
        self.sim.engine_on = not self.sim.engine_on
        self.start_btn.config(text=("Stop Engine" if self.sim.engine_on
                                    else "Start Engine"))
        if not self.sim.engine_on: self.sim._rpm = 0

    def _upshift(self):   self.sim.upshift()
    def _downshift(self): self.sim.downshift()
    def _change_engine(self,disp,*_):
        self.sim.load_engine(self.disp_to_key.get(disp,None))

    # recording
    def _start_rec(self):
        self.recording = True
        self.t=0.0; self.ts,self.hp_hist,self.rpm_hist = [], [], []
        self.line.set_data([], []); self.ax.relim(); self.ax.autoscale_view()
        self.canvas.draw()

    def _stop_rec(self):
        if not (self.recording and self.ts): self.recording=False; return
        self.recording=False
        default=f"sim_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path=filedialog.asksaveasfilename(defaultextension=".csv",
                                          initialfile=default,
                                          filetypes=[("CSV","*.csv")])
        if not path:return
        with open(path,"w",newline="") as f:
            w=csv.writer(f); w.writerow(["time_s","rpm","hp"])
            w.writerows(zip(self.ts,self.rpm_hist,self.hp_hist))
        messagebox.showinfo("Export",
                            f"Saved {len(self.ts)} samples to:\n{path}")
