import csv, time, tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pathlib import Path

from engine.simulator import EngineSimulator
from engine import engine_registry as reg  # renamed import
                                             # (scan_engines, add_engine)


class TunerWindow(tk.Frame):
    """UI with red-line RPM bar, numeric HP, smooth graph, Dyno sweep & Engine wizard."""

    # ───────── init ─────────
    def __init__(self, master: tk.Tk):
        super().__init__(master); self.pack(fill="both", expand=True)

        self.sim = EngineSimulator()
        self._refresh_engine_list()

        # recording & sweep
        self.recording = False
        self.dyno_sweep = False
        self.t = 0.0
        self.ts, self.hp_hist, self.rpm_hist = [], [], []

        self._init_styles()
        self._build_ui()
        self._loop()

    # ───────── engines helper ─────────
    def _refresh_engine_list(self):
        self.engines = reg.scan_engines()
        self.disp_to_key = {m["display"]: k for k, m in self.engines.items()}
        self.disp_opts = list(self.disp_to_key) or ["default"]
        self.engine_var = tk.StringVar(value=self.disp_opts[0])

    # ───────── ttk styles ─────────
    def _init_styles(self):
        s = ttk.Style()
        s.configure("RPMGreen.Horizontal.TProgressbar",
                    troughcolor="#ddd", background="limegreen")
        s.configure("RPMRed.Horizontal.TProgressbar",
                    troughcolor="#ddd", background="red")

    # ───────── UI build ─────────
    def _slider(self, label, frm, to, init, res=1):
        w = tk.Scale(self, from_=frm, to=to, resolution=res,
                     orient="horizontal", label=label)
        w.set(init); w.pack(fill="x", padx=8); return w

    def _build_ui(self):
        # sliders
        self.throttle = self._slider("Throttle (%)", 0, 100, 0)
        self.timing   = self._slider("Timing (°BTDC)", 0, 30, 10)
        self.afr      = self._slider("AFR", 10, 16, 13.5, 0.1)
        self.boost    = self._slider("Boost (PSI)", 0, 20, 5)

        # gear row
        g = tk.Frame(self); g.pack(pady=6)
        tk.Button(g, text="▼", width=4, command=self.sim.downshift).pack(side="left")
        self.gear_lbl = tk.Label(g, text="Gear: N",
                                 font=("Helvetica",16,"bold"), width=9)
        self.gear_lbl.pack(side="left", padx=6)
        tk.Button(g, text="▲", width=4, command=self.sim.upshift).pack(side="left")

        # engine selector + add wizard
        e = tk.Frame(self); e.pack(pady=4)
        tk.Label(e, text="Engine:").pack(side="left")
        self.engine_menu = tk.OptionMenu(e, self.engine_var, *self.disp_opts,
                                         command=self._change_engine)
        self.engine_menu.pack(side="left")
        tk.Button(e, text="Add Engine…",
                  command=self._engine_wizard).pack(side="left", padx=6)

        # start/stop + sweep
        btn_row = tk.Frame(self); btn_row.pack(pady=6)
        self.start_btn = tk.Button(btn_row, text="Start Engine",
                                   width=12, command=self._toggle_engine)
        self.start_btn.pack(side="left", padx=4)
        tk.Button(btn_row, text="Dyno Sweep", width=12,
                  command=self._start_dyno).pack(side="left", padx=4)

        # record
        r = tk.Frame(self); r.pack(pady=4)
        tk.Button(r, text="Start Rec", width=12,
                  command=self._start_rec).pack(side="left", padx=4)
        tk.Button(r, text="Stop / Export", width=12,
                  command=self._stop_rec).pack(side="left")

        # gauges & graph
        self._add_gauges()
        self._add_graph()

    # ───────── gauges ─────────
    def _add_gauges(self):
        g = tk.Frame(self); g.pack(pady=10)

        tk.Label(g, text="RPM").pack(anchor="w")
        self.rpm_bar = ttk.Progressbar(g, orient="horizontal", length=500,
                                       maximum=self.sim.redline,
                                       style="RPMGreen.Horizontal.TProgressbar")
        self.rpm_bar.pack(pady=2)
        self.rpm_num = tk.Label(g, text="0",
                                font=("Helvetica",14,"bold"), fg="black")
        self.rpm_num.pack(anchor="e", pady=2)

        self.hp_num = tk.Label(g, text="HP: --",
                               font=("Helvetica",14,"bold"))
        self.hp_num.pack(anchor="w", pady=4)

        self.kn_lbl = tk.Label(g, text="Knock: --", font=("Helvetica",12))
        self.mpg_lbl= tk.Label(g, text="Fuel Eff: -- MPG", font=("Helvetica",12))
        self.kn_lbl.pack(anchor="w"); self.mpg_lbl.pack(anchor="w")

    # ───────── graph ─────────
    def _add_graph(self):
        fig = Figure(figsize=(8,4), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)"); self.ax.set_ylabel("HP")
        self.ax.grid(True)
        (self.line,) = self.ax.plot([],[], lw=2)
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(pady=6)

    # ───────── runtime loop ─────────
    def _loop(self):
        # dyno sweep ramp
        if self.dyno_sweep:
            self.sim.throttle += 1.25   # 0→100 in ~8 s (0.2 s per frame)
            if self.sim.throttle >= 100:
                self.sim.throttle = 100
                self._end_dyno()

        # UI → sim (for manual mode)
        if not self.dyno_sweep:
            self.sim.throttle = self.throttle.get()
        self.sim.timing    = self.timing.get()
        self.sim.afr       = self.afr.get()
        self.sim.boost_cmd = self.boost.get()

        hp, knock, mpg, rpm = self.sim.step(0.2)
        self._update_gauges(hp, rpm)

        if self.recording:
            self.ts.append(self.t); self.hp_hist.append(hp); self.rpm_hist.append(rpm)
            self._update_graph()

        self.kn_lbl.config(text=f"Knock: {knock}")
        self.mpg_lbl.config(text=f"Fuel Eff: {mpg:.1f} MPG")
        self.gear_lbl.config(text=f"Gear: {self.sim.gear}")

        self.t += 0.2
        self.after(200, self._loop)

    # ───────── gauge update ─────────
    def _update_gauges(self, hp, rpm):
        over = rpm >= 0.95*self.sim.redline
        bar_style = "RPMRed.Horizontal.TProgressbar" if over else "RPMGreen.Horizontal.TProgressbar"
        self.rpm_bar.configure(style=bar_style, maximum=self.sim.redline, value=rpm)
        self.rpm_num.config(text=f"{rpm:.0f}", fg=("red" if over else "black"))
        self.hp_num.config(text=f"HP: {hp:.1f}")

    # ───────── graph update ─────────
    def _update_graph(self):
        self.line.set_data(self.ts, self.hp_hist)
        self.ax.relim(); self.ax.autoscale_view()
        self.canvas.draw_idle()

    # ───────── button callbacks ─────────
    def _toggle_engine(self):
        self.sim.engine_on = not self.sim.engine_on
        self.start_btn.config(text=("Stop Engine" if self.sim.engine_on else "Start Engine"))
        if not self.sim.engine_on: self.sim._rpm = 0

    def _change_engine(self, disp,*_):
        self.sim.load_engine(self.disp_to_key.get(disp))

    # ---- dyno sweep ----
    def _start_dyno(self):
        if not self.sim.engine_on:
            messagebox.showinfo("Dyno Sweep", "Start the engine first!")
            return
        self.dyno_sweep = True
        self.sim.throttle = 0
        self._start_rec()          # record sweep

    def _end_dyno(self):
        self.dyno_sweep = False
        self._stop_rec()           # export sweep first
        # show HP vs RPM curve
        win = tk.Toplevel(self); win.title("Dyno Sheet")
        fig = Figure(figsize=(6,4), dpi=100)
        ax  = fig.add_subplot(111)
        ax.set_xlabel("RPM"); ax.set_ylabel("HP"); ax.grid(True)
        ax.plot(self.rpm_hist, self.hp_hist, lw=2)
        canvas = FigureCanvasTkAgg(fig, master=win); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---- recording ----
    def _start_rec(self):
        self.recording=True
        self.t=0.0; self.ts,self.hp_hist,self.rpm_hist=[],[],[]
        self.line.set_data([],[]); self.ax.relim(); self.canvas.draw()

    def _stop_rec(self):
        if not (self.recording and self.ts):
            self.recording=False; return
        self.recording=False
        default=f"sim_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path=filedialog.asksaveasfilename(defaultextension=".csv",
                initialfile=default,filetypes=[("CSV","*.csv")])
        if path:
            with open(path,"w",newline="") as f:
                w=csv.writer(f); w.writerow(["time_s","rpm","hp"])
                w.writerows(zip(self.ts,self.rpm_hist,self.hp_hist))
            messagebox.showinfo("Export", f"Saved {len(self.ts)} samples to:\n{path}")

    # ---- add-engine wizard ----
    def _engine_wizard(self):
        dlg = tk.Toplevel(self); dlg.title("Add New Engine")
        tk.Label(dlg, text="Engine Name:").grid(row=0, column=0, sticky="e")
        tk.Label(dlg, text="Idle RPM:").grid( row=1, column=0, sticky="e")
        tk.Label(dlg, text="Redline RPM:").grid(row=2, column=0, sticky="e")
        tk.Label(dlg, text="Torque CSV:").grid(row=3, column=0, sticky="e")

        name = tk.Entry(dlg, width=25); name.grid(row=0, column=1, pady=2)
        idle = tk.Entry(dlg, width=10); idle.grid(row=1, column=1, pady=2)
        redl = tk.Entry(dlg, width=10); redl.grid(row=2, column=1, pady=2)
        csv_path = tk.StringVar()
        tk.Entry(dlg, textvariable=csv_path, width=25).grid(row=3,column=1,pady=2)
        tk.Button(dlg, text="Browse",
                  command=lambda: csv_path.set(filedialog.askopenfilename(
                      filetypes=[("CSV","*.csv")] ))
                  ).grid(row=3,column=2,padx=4)

        def save():
            try:
                key = reg.add_engine(name.get(), int(idle.get()),
                                     int(redl.get()), Path(csv_path.get()))
            except Exception as e:
                messagebox.showerror("Add Engine", str(e)); return
            dlg.destroy()
            self._refresh_engine_list()
            # rebuild OptionMenu
            menu = self.engine_menu["menu"]
            menu.delete(0, "end")
            for disp in self.disp_opts:
                menu.add_command(label=disp,
                                 command=lambda d=disp: self.engine_var.set(d))
            self.engine_var.set(self.engines[key]["display"])
            self._change_engine(self.engine_var.get())

        tk.Button(dlg, text="Save", command=save).grid(row=4,column=0,columnspan=3,pady=6)
