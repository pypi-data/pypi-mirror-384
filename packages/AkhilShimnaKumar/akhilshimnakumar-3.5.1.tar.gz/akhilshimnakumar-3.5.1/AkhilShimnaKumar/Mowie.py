import math
from math import sin, cos, pi
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Mowie:
    def __init__(self):
        """Change these values according to the requirements"""
        self.m_initial = 10        # Initial mass of the robot in Kg
        self.slope = 25            # Slope requirement in deg
        self.obstacle_height = 0.05  # Obstacle height in m (5 cm)
        self.SF = 1.25             # Safety factor for calculations
        self.mu_grass = 0.5        # Friction coefficient of grass
        self.battery_voltage = 24  # Battery voltage in volts
        self.g = 9.80665           # Acceleration due to gravity

        self.initialisation_helper()
        self.print_torque_matrix()

        # GUI
        self.create_gui()

    def initialisation_helper(self):
        self.mu = self.mu_grass
        self.m = self.m_initial
        self.torque_array = []
        self.motor_specs = []
        self.required_wheel_radius = None

    # --- Torque calculations ---
    def climb(self, wheel_radius):
        """Torque required to climb a slope (per motor)."""
        F = self.m * self.g * (sin(math.radians(self.slope)) + self.mu * cos(math.radians(self.slope)))
        T = F * wheel_radius
        return T / 4

    def obstacle_crossing(self, wheel_radius):
        """Torque required to climb over an obstacle (per motor)."""
        if wheel_radius <= self.obstacle_height:
            return float('inf')  # impossible
        # approximate torque needed to lift robot over obstacle
        T = self.m * self.g * (wheel_radius - self.obstacle_height)
        return T / 4

    # --- Table generator ---
    def print_torque_matrix(self):
        self.torque_table = []
        self.torque_array = []

        wheel_radius = 0.01  # start from 1 cm
        for _ in range(0, 30):
            array = [
                wheel_radius * 100,  # cm for display
                self.climb(wheel_radius) * self.SF,
                self.obstacle_crossing(wheel_radius) * self.SF
            ]
            self.torque_array.append(array)
            self.torque_table.append(array)
            wheel_radius += 0.01  # step = 1 cm

    # --- Motor selection ---
    def motor_database(self, torque):
        self.motor_data = np.array([
            [1200, 1.5, 0.5, 8],
            [450, 5, 0.5, 20],
            [240, 10, 0.5, 35],
            [130, 20, 0.5, 50],
            [80, 35, 0.5, 70],
            [45, 55, 0.5, 90],
            [30, 70, 0.5, 110],
            [18, 85, 0.5, 130],
            [12, 90, 0.5, 150],
            [9, 100, 0.5, 170]
        ])
        # Convert rated torque to Nm
        self.motor_data[:, 1] = self.motor_data[:, 1] * 0.0980665

        rated_torques = self.motor_data[:, 1]
        i = np.abs(rated_torques - torque).argmin()
        if torque >= rated_torques[i]:
            return self.motor_data[i]
        else:
            if i + 1 < len(self.motor_data):
                return self.motor_data[i + 1]
            else:
                print("Current motor database doesn't have a suitable motor")
                return None

    # --- Set chosen wheel radius ---
    def set_wheel_radius(self, radius_cm):
        self.required_wheel_radius = float(radius_cm) / 100  # convert cm -> m
        torque_array_np = np.array(self.torque_array)
        i = np.argmin(np.abs(torque_array_np[:, 0] - radius_cm))
        torque = max(torque_array_np[i, 1], torque_array_np[i, 2])
        self.motor_specs = self.motor_database(torque)

    def update_motor_info(self):
        self.motor_info.delete(1.0, tk.END)
        if self.motor_specs is None:
            self.motor_info.insert(tk.END, "No suitable motor found in the database.\n")
            return

        headers = ["RPM", "Rated Torque (Nm)", "Rated Current (A)", "Ultimate Torque (Nm)"]
        self.motor_info.insert(tk.END, f"{headers[0]:<8} {headers[1]:<18} {headers[2]:<18} {headers[3]:<18}\n")
        self.motor_info.insert(tk.END, "-" * 65 + "\n")
        self.motor_info.insert(
            tk.END,
            f"{int(self.motor_specs[0]):<8} {self.motor_specs[1]:<18.2f} "
            f"{self.motor_specs[2]:<18.2f} {self.motor_specs[3]:<18.2f}\n"
        )

        speed = (2 * pi * self.required_wheel_radius * self.motor_specs[0] / 60)
        power = self.battery_voltage * self.motor_specs[2]
        self.motor_info.insert(tk.END, f"\nThe robot will move with a speed of {speed:.2f} m/s.\n")
        self.motor_info.insert(tk.END, f"Each motor needs nominal power of {power:.2f} W.\n")

    # --- Plotting ---
    def plot_torques(self, highlight_radius=None):
        torque_array_np = np.array(self.torque_array)
        radius = torque_array_np[:, 0]
        slope_torque = torque_array_np[:, 1]
        obstacle_torque = torque_array_np[:, 2]

        self.ax.clear()
        self.ax.plot(radius, slope_torque, label="Slope Torque")
        self.ax.plot(radius, obstacle_torque, label="Obstacle Torque")

        if highlight_radius is not None:
            i = np.argmin(np.abs(radius - highlight_radius))
            self.ax.plot(radius[i], slope_torque[i], 'ro', label="Selected Slope Torque")
            self.ax.plot(radius[i], obstacle_torque[i], 'go', label="Selected Obstacle Torque")

        self.ax.set_xlabel("Wheel Radius (cm)")
        self.ax.set_ylabel("Torque (Nm)")
        self.ax.set_title("Torque vs Wheel Radius")
        self.ax.legend()
        self.canvas.draw()

    def on_set_radius(self):
        try:
            radius = float(self.radius_entry.get())
        except ValueError:
            self.motor_info.delete(1.0, tk.END)
            self.motor_info.insert(tk.END, "Please enter a valid number.\n")
            return
        self.set_wheel_radius(radius)
        self.update_motor_info()
        self.plot_torques(highlight_radius=radius)

    # --- GUI creation ---
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Mowie Robot Torque Analysis")
        self.root.geometry("1500x800")

        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Parameter Inputs ---
        params_frame = tk.LabelFrame(left_frame, text="Robot Parameters", padx=10, pady=10)
        params_frame.pack(pady=10, fill=tk.X)

        self.param_entries = {}

        params = [
            ("Initial Mass (kg)", "m_initial"),
            ("Slope (deg)", "slope"),
            ("Obstacle Height (cm)", "obstacle_height"),
            ("Safety Factor", "SF"),
            ("Friction Coefficient (Grass)", "mu_grass"),
            ("Battery Voltage (V)", "battery_voltage"),
            ("Gravity (m/s²)", "g"),
        ]

        for i, (label_text, attr) in enumerate(params):
            col = i % 2
            row = i // 2
            label = tk.Label(params_frame, text=label_text, anchor="w", width=25)
            label.grid(row=row, column=col * 2, sticky="w", padx=5, pady=3)
            entry = tk.Entry(params_frame, width=10)
            val = getattr(self, attr) * 100 if attr == "obstacle_height" else getattr(self, attr)
            entry.insert(0, val)
            entry.grid(row=row, column=col * 2 + 1, sticky="w", padx=5, pady=3)
            self.param_entries[attr] = entry

        tk.Button(params_frame, text="Update Parameters", command=self.update_parameters).grid(
            row=(len(params) // 2) + 1, column=0, columnspan=4, pady=8
        )

        # --- Wheel Radius Input ---
        radius_frame = tk.Frame(left_frame)
        radius_frame.pack(pady=10, fill=tk.X)
        tk.Label(radius_frame, text="Enter wheel radius (cm):").pack(side=tk.LEFT, padx=5)
        self.radius_entry = tk.Entry(radius_frame, width=10)
        self.radius_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(radius_frame, text="Set Wheel Radius", command=self.on_set_radius).pack(side=tk.LEFT, padx=5)

        # --- Motor Info ---
        self.motor_info = tk.Text(left_frame, width=70, height=8)
        self.motor_info.pack(pady=10, fill=tk.X)

        # --- Plot Frame ---
        plot_frame = tk.Frame(left_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.plot_torques()

        # --- Torque Table ---
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.torque_text = scrolledtext.ScrolledText(right_frame, width=70, height=35)
        self.torque_text.pack(fill=tk.BOTH, expand=True)
        self.display_torque_table()

    def update_parameters(self):
        """Fetch updated parameters from GUI and recalculate"""
        try:
            self.m_initial = float(self.param_entries["m_initial"].get())
            self.slope = float(self.param_entries["slope"].get())
            self.obstacle_height = float(self.param_entries["obstacle_height"].get()) / 100  # cm -> m
            self.SF = float(self.param_entries["SF"].get())
            self.mu_grass = float(self.param_entries["mu_grass"].get())
            self.battery_voltage = float(self.param_entries["battery_voltage"].get())
            self.g = float(self.param_entries["g"].get())
        except ValueError:
            self.motor_info.delete(1.0, tk.END)
            self.motor_info.insert(tk.END, "Please enter valid numeric values for parameters.\n")
            return

        self.initialisation_helper()
        self.print_torque_matrix()
        self.display_torque_table()
        self.plot_torques()

        self.motor_info.delete(1.0, tk.END)
        self.motor_info.insert(tk.END, "Parameters updated successfully.\n")

    def display_torque_table(self):
        self.torque_text.delete(1.0, tk.END)
        header = f"{'Wheel Radius (cm)':>20} {'Slope Torque (Nm)':>20} {'Obstacle Torque (Nm)':>25}\n"
        self.torque_text.insert(tk.END, header)
        self.torque_text.insert(tk.END, "-" * 70 + "\n")
        for row in self.torque_table:
            self.torque_text.insert(tk.END, f"{row[0]:>20.0f} {row[1]:>20.2f} {row[2]:>25.2f}\n")


# --- Launch Mowie with GUI ---
if __name__ == "__main__":
    mowie = Mowie()
