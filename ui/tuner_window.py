import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random
import json
import os

from ui.rpm_gauge import RPMGauge

PROFILE_DIR = "assets/profiles"

class TunerWindow:
    def __init__(self, root):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        root.title("Simulated Engine Tuner")
        root.geometry("1000x600")

        # Gear and vehicle setup
        self.current_gear = 1
        self.max_gear = 6
        self.gear_ratios = {
            1: 3.82,
            2: 2.20,
            3: 1.52,
            4: 1.22,
            5: 1.00,
            6: 0.63
        }
        self.vehicle_speed = 0  # km/h (initially stopped)
        self.boost_level = 12.0
        self.turbo_map = "Balanced"
        self.turbo_maps = {
            "Fast Spool": lambda rpm: min(400 + rpm * 0.08, 500),
            "Balanced": lambda rpm: min(300 + rpm * 0.06, 480),
            "High-End": lambda rpm: max(200, min(rpm * 0.05, 460))
        }

        self.simulation_running = False

        # Sidebar
        self.sidebar = ctk.CTkFrame(root, width=200)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="Tuner", font=("Arial", 24)).pack(pady=20)

        for name in ["Dashboard", "Tuning", "Graph", "Settings"]:
            ctk.CTkButton(self.sidebar, text=name, command=lambda n=name: self.select_tab(n)).pack(pady=10, fill="x", padx=10)

        # Main area
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.tabs = ctk.CTkTabview(self.main_frame)
        self.tabs.pack(fill="both", expand=True)

        # Initialize tabs
        self._init_dashboard_tab()
        self._init_tuning_tab()
        self._init_graph_tab()
        self._init_settings_tab()

    def _init_dashboard_tab(self):
        dashboard = self.tabs.add("Dashboard")

        self.rpm_gauge = RPMGauge(dashboard, max_rpm=8000)
        self.rpm_gauge.pack(pady=10)

        self.rpm_label = ctk.CTkLabel(dashboard, text="RPM: 0", font=("Consolas", 28))
        self.rpm_label.pack(pady=10)

        self.boost_label = ctk.CTkLabel(dashboard, text="Boost: 0.0 PSI", font=("Consolas", 24))
        self.boost_label.pack(pady=5)

        self.gear_label = ctk.CTkLabel(dashboard, text="Gear: 1", font=("Consolas", 24))
        self.gear_label.pack(pady=10)

        gear_frame = ctk.CTkFrame(dashboard)
        gear_frame.pack(pady=5)
        ctk.CTkButton(gear_frame, text="Shift -", command=self.shift_down).pack(side="left", padx=5)
        ctk.CTkButton(gear_frame, text="Shift +", command=self.shift_up).pack(side="left", padx=5)

        self.knock_label = ctk.CTkLabel(dashboard, text="⚠ Knock Detected!", text_color="red", font=("Arial", 20))
        self.knock_label.pack(pady=10)
        self.knock_label.pack_forget()

        # Driving simulation toggle
        ctk.CTkButton(dashboard, text="Start Driving Simulation", command=self.toggle_driving_simulation).pack(pady=10)

    def _init_tuning_tab(self):
        tuning = self.tabs.add("Tuning")

        def update_boost(val):
            self.boost_level = val
            self.boost_value.configure(text=f"{val:.1f} PSI")

        ctk.CTkLabel(tuning, text="Boost Level").pack(pady=5)
        self.boost_slider = ctk.CTkSlider(tuning, from_=0, to=30, command=update_boost)
        self.boost_slider.set(self.boost_level)
        self.boost_slider.pack()
        self.boost_value = ctk.CTkLabel(tuning, text=f"{self.boost_level:.1f} PSI")
        self.boost_value.pack(pady=5)

        ctk.CTkLabel(tuning, text="Turbo Map").pack(pady=10)
        self.turbo_selector = ctk.CTkOptionMenu(tuning, values=list(self.turbo_maps.keys()), command=self.set_turbo_map)
        self.turbo_selector.set(self.turbo_map)
        self.turbo_selector.pack(pady=5)

        ctk.CTkButton(tuning, text="Save Profile", command=self.save_profile).pack(pady=5)
        ctk.CTkButton(tuning, text="Load Profile", command=self.load_profile).pack(pady=5)

    def _init_graph_tab(self):
        graph = self.tabs.add("Graph")

        fig, ax = plt.subplots()
        ax.set_title("Torque vs RPM")
        ax.set_xlabel("RPM")
        ax.set_ylabel("Torque (Nm)")
        ax.grid(True)
        ax.plot([1000, 2000, 3000, 4000, 5000], [200, 350, 420, 400, 360])

        canvas = FigureCanvasTkAgg(fig, master=graph)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def _init_settings_tab(self):
        settings = self.tabs.add("Settings")
        ctk.CTkLabel(settings, text="Appearance Mode").pack(pady=5)
        appearance_menu = ctk.CTkOptionMenu(settings, values=["System", "Light", "Dark"],
                                            command=ctk.set_appearance_mode)
        appearance_menu.pack(pady=5)

    def select_tab(self, name):
        self.tabs.set(name)

    def shift_up(self):
        if self.current_gear < self.max_gear:
            self.current_gear += 1
            self.update_gear_display()

    def shift_down(self):
        if self.current_gear > 1:
            self.current_gear -= 1
            self.update_gear_display()

    def update_gear_display(self):
        self.gear_label.configure(text=f"Gear: {self.current_gear}")

    def set_turbo_map(self, map_name):
        self.turbo_map = map_name

    def check_knock(self, rpm):
        if rpm > 6500 and self.boost_level > 20:
            self.knock_label.pack()
        else:
            self.knock_label.pack_forget()

    def toggle_driving_simulation(self):
        self.simulation_running = not self.simulation_running
        if self.simulation_running:
            self.vehicle_speed = 0
            self.simulate_driving()

    def simulate_driving(self):
        if not self.simulation_running:
            return

        self.vehicle_speed += 2  # accelerate
        if self.vehicle_speed > 120:
            self.vehicle_speed = 0
            self.current_gear = 1
        elif self.vehicle_speed > 20 * self.current_gear and self.current_gear < self.max_gear:
            self.current_gear += 1
        self.update_gear_display()

        self.update_engine_display()
        self.main_frame.after(300, self.simulate_driving)

    def update_engine_display(self):
        speed_mps = self.vehicle_speed * 1000 / 3600
        final_drive = 3.73
        tire_circumference = 2.1

        gear_ratio = self.gear_ratios[self.current_gear]
        wheel_rpm = speed_mps / tire_circumference * 60
        engine_rpm = wheel_rpm * gear_ratio * final_drive
        engine_rpm = int(min(engine_rpm, 8000))

        torque = self.turbo_maps[self.turbo_map](engine_rpm)

        self.rpm_gauge.update_needle(engine_rpm)
        self.rpm_label.configure(text=f"RPM: {engine_rpm}")
        self.gear_label.configure(text=f"Gear: {self.current_gear}")
        self.boost_label.configure(text=f"Boost: {self.boost_level:.1f} PSI")

        self.check_knock(engine_rpm)

    def save_profile(self):
        os.makedirs(PROFILE_DIR, exist_ok=True)
        profile_data = {
            "boost_level": self.boost_level,
            "gear_ratios": self.gear_ratios,
            "turbo_map": self.turbo_map
        }
        with open(os.path.join(PROFILE_DIR, "custom_profile.json"), "w") as f:
            json.dump(profile_data, f, indent=4)

    def load_profile(self):
        filepath = os.path.join(PROFILE_DIR, "custom_profile.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                profile = json.load(f)
                self.boost_level = profile.get("boost_level", self.boost_level)
                self.gear_ratios = profile.get("gear_ratios", self.gear_ratios)
                self.turbo_map = profile.get("turbo_map", self.turbo_map)

                self.boost_slider.set(self.boost_level)
                self.boost_value.configure(text=f"{self.boost_level:.1f} PSI")
                self.turbo_selector.set(self.turbo_map)
                self.update_gear_display()
