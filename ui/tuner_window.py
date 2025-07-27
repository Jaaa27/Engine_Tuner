import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class TunerWindow:
    def __init__(self, root):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        root.title("Simulated Engine Tuner")
        root.geometry("1000x600")

        # Sidebar
        self.sidebar = ctk.CTkFrame(root, width=200)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="Tuner", font=("Arial", 24)).pack(pady=20)

        for name in ["Dashboard", "Tuning", "Graph", "Settings"]:
            ctk.CTkButton(self.sidebar, text=name, command=lambda n=name: self.select_tab(n)).pack(pady=10, fill="x", padx=10)

        # Main area with TabView
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.tabs = ctk.CTkTabview(self.main_frame)
        self.tabs.pack(fill="both", expand=True)

        self._init_dashboard_tab()
        self._init_tuning_tab()
        self._init_graph_tab()
        self._init_settings_tab()

    def _init_dashboard_tab(self):
        dashboard = self.tabs.add("Dashboard")
        self.rpm_label = ctk.CTkLabel(dashboard, text="RPM: 3500", font=("Consolas", 32))
        self.rpm_label.pack(pady=20)

        self.boost_label = ctk.CTkLabel(dashboard, text="Boost: 12.4 PSI", font=("Consolas", 24))
        self.boost_label.pack()

    def _init_tuning_tab(self):
        tuning = self.tabs.add("Tuning")

        def update_boost(val):
            self.boost_value.configure(text=f"{val:.1f} PSI")

        ctk.CTkLabel(tuning, text="Boost Level").pack(pady=5)
        boost_slider = ctk.CTkSlider(tuning, from_=0, to=30, command=update_boost)
        boost_slider.pack()
        self.boost_value = ctk.CTkLabel(tuning, text="12.0 PSI")
        self.boost_value.pack(pady=5)

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
