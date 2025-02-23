import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from bms_core.battery_cell import Cell  # ✅ Import the central Cell class correctly

# ✅ Constants for Activation and Concentration Overpotential
R = 8.314  # Universal Gas Constant (J/mol·K)
F = 96485  # Faraday's Constant (C/mol)
T = 298  # Temperature in Kelvin
alpha = 0.5  # Charge transfer coefficient
z = 1  # Number of electrons per reaction
I0 = 0.01  # Exchange current density (A)

# ✅ Create a centralized `Cell` instance
cell_used = Cell(chemistry="NMC")

def activation_overpotential(current):
    """Calculate activation overpotential safely."""
    if abs(current) < 1e-6:  # Prevent log(0) error
        return 0
    V_act = (R * T / (alpha * z * F)) * np.log(abs(current) / I0 + 1)
    return V_act

def concentration_overpotential(Cs, Cb):
    """Calculate concentration overpotential safely."""
    if Cs <= 0 or Cb <= 0:
        return 0
    V_conc = (R * T / (z * F)) * np.log(Cs / Cb)
    return V_conc

def compute_voltage(soc, current, ocv_lookup, internal_resistance):
    """Compute terminal voltage considering OCV lookup and overpotential losses."""

    # ✅ Ensure SOC is within valid range
    soc = max(0, min(100, soc))

    # ✅ Convert SOC keys to integers
    soc_keys = list(map(int, ocv_lookup.keys()))
    closest_soc = min(soc_keys, key=lambda x: abs(x - soc))
    ocv = ocv_lookup[str(closest_soc)]

    # ✅ Debugging: Print OCV Selection
    print(f"DEBUG: SOC = {soc:.2f}%, Closest SOC = {closest_soc}%, OCV = {ocv:.3f}V")

    # ✅ Ensure Internal Resistance is Properly Converted
    if internal_resistance > 1:  # If >1Ω, assume it's in Ω
        V_ohm = current * internal_resistance
    else:  # If small, assume it's in mΩ and convert
        V_ohm = current * (internal_resistance / 1000)

    # ✅ Debugging: Print Ohmic Drop Calculation
    print(f"DEBUG: Current = {current}A, Internal Resistance = {internal_resistance}Ω, Ohmic Drop = {V_ohm:.3f}V")

    # ✅ Final Voltage Calculation
    voltage = ocv - V_ohm
    return voltage



def update_soc(soc, current, dt, nominal_capacity):
    """Update SOC based on current."""
    new_soc = soc + (current * dt) / (nominal_capacity * 3600)
    return max(0, min(100, new_soc))

class ChargingSimulation:
    def __init__(self, cell = cell_used, charge_current=5, dt=60, sim_time=360000, mode="CC-CV"):
        """
        :param cell: Cell object (single module)
        :param charge_current: Charging current in Amperes
        :param dt: Time step in seconds
        :param sim_time: Total simulation time in seconds
        :param mode: "CC", "CV", or "CC-CV"
        """
        self.cell = cell
        self.charge_current = charge_current
        self.dt = dt
        self.sim_time = sim_time
        self.mode = mode
        self.current_time = 0

        # Store data
        self.time_data = []
        self.soc_data = []
        self.voltage_data = []
        self.current_data = []

    def simulate(self):
        """Simulate the battery charging cycle."""
        current = self.charge_current
        while self.current_time < self.sim_time:
            # Compute new voltage
            soc = self.cell.soc
            voltage = compute_voltage(20, current, self.cell.ocv_lookup, self.cell.internal_resistance)

            # Switch to CV Mode if CC-CV
            if self.mode == "CC-CV" and voltage >= 4.2:
                self.mode = "CV"
                print(f"Switching to CV Mode at {self.current_time}s")

            # Constant Voltage Mode: Adjust Current
            if self.mode == "CV":
                max_voltage = 4.2  # Cutoff voltage
                current = (max_voltage - voltage) / (self.cell.internal_resistance / 1000)
                current = max(0, current)  # Ensure no negative current

            # Update SOC
            self.cell.soc = update_soc(self.cell.soc, current, self.dt, self.cell.nominal_capacity)

            # Store values
            self.time_data.append(self.current_time)
            self.soc_data.append(self.cell.soc)
            self.voltage_data.append(voltage)
            self.current_data.append(current)

            # Print values
        #    print(f"Time: {self.current_time}s, SOC: {self.cell.soc:.2f}%, Voltage: {voltage:.2f}V, Current: {current:.2f}A")

            self.current_time += self.dt
            time.sleep(0.05)  # Simulate real-time behavior

        self.plot_results()

    def plot_results(self):
        """Plot SOC and Voltage vs. Time."""
        fig, ax1 = plt.subplots()
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("SOC (%)", color="tab:blue")
        ax1.plot(self.time_data, self.soc_data, color="tab:blue")
        ax1.tick_params(axis="y", labelcolor="tab:blue")

        ax2 = ax1.twinx()
        ax2.set_ylabel("Voltage (V)", color="tab:red")
        ax2.plot(self.time_data, self.voltage_data, color="tab:red")
        ax2.tick_params(axis="y", labelcolor="tab:red")

        plt.title(f"Battery {self.mode} Charging Simulation")
        plt.show()

cccv_simulation = ChargingSimulation(cell_used, charge_current=500, dt=60, sim_time=10000, mode="CC-CV")
cccv_simulation.simulate()