import customtkinter as ctk
import tkinter as tk
import math

class RPMGauge(ctk.CTkFrame):
    def __init__(self, master, max_rpm=8000, size=250, **kwargs):
        super().__init__(master, **kwargs)
        self.max_rpm = max_rpm
        self.size = size
        self.rpm = 0

        self.canvas = tk.Canvas(self, width=size, height=size, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.center = size // 2
        self.radius = size // 2 - 10

        self.needle = None
        self.draw_static_elements()
        self.update_needle(0)

    def draw_static_elements(self):
        # Draw outer circle
        self.canvas.create_oval(10, 10, self.size - 10, self.size - 10, outline="white", width=2)

        # Draw RPM ticks
        for i in range(0, self.max_rpm + 1, 1000):
            angle = self._rpm_to_angle(i)
            x1, y1 = self._polar_to_cartesian(angle, self.radius - 10)
            x2, y2 = self._polar_to_cartesian(angle, self.radius - 2)
            self.canvas.create_line(x1, y1, x2, y2, fill="white", width=2)

            # Label
            lx, ly = self._polar_to_cartesian(angle, self.radius - 25)
            self.canvas.create_text(lx, ly, text=str(i // 1000), fill="white", font=("Arial", 10))

    def update_needle(self, rpm):
        # Clamp RPM
        rpm = max(0, min(rpm, self.max_rpm))
        self.rpm = rpm

        # Remove old needle
        if self.needle:
            self.canvas.delete(self.needle)

        # Draw new needle
        angle = self._rpm_to_angle(rpm)
        x, y = self._polar_to_cartesian(angle, self.radius - 20)
        self.needle = self.canvas.create_line(self.center, self.center, x, y, fill="red", width=3)

    def _rpm_to_angle(self, rpm):
        # Map 0-RPM to -120° to +120° (240° sweep)
        ratio = rpm / self.max_rpm
        return math.radians(240 * ratio - 120)

    def _polar_to_cartesian(self, angle, length):
        x = self.center + length * math.cos(angle)
        y = self.center + length * math.sin(angle)
        return x, y
