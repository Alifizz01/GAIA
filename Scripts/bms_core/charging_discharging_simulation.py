import sys
import os
import time
import numpy as np

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
    print(f"Activation Overpotential: {V_act:.6f} V")  # ✅ Debugging
    return V_act

def concentration_overpotential(Cs, Cb):
    """Calculate concentration overpotential safely."""
    if Cs <= 0 or Cb <= 0:
        return 0
    V_conc = (R * T / (z * F)) * np.log(Cs / Cb)
    print(f"Concentration Overpotential: {V_conc:.6f} V")  # ✅ Debugging
    return V_conc

def compute_voltage(soc, current, ocv_lookup, internal_resistance):
    """Compute terminal voltage considering overpotentials."""
    soc = max(0, min(100, soc))  # Ensure SOC is within valid range
    soc_keys = list(map(int, ocv_lookup.keys()))
    closest_soc = min(soc_keys, key=lambda x: abs(x - soc))
    ocv = ocv_lookup[str(closest_soc)]

    print(f"OCV at SOC={soc:.1f}%: {ocv:.3f}V")  # ✅ Debugging

    V_act = activation_overpotential(current)  # Activation Loss
    V_conc = concentration_overpotential(1.0, 0.9)  # Assume small concentration drop
    V_ohm = current * internal_resistance  # Ohmic Drop

    print(f"Ohmic Drop: {V_ohm:.6f} V")  # ✅ Debugging

    # Final Terminal Voltage
    voltage = ocv - V_act - V_conc - V_ohm
    return voltage

# ✅ Accessing attributes properly from `cell_used`
final_voltage = compute_voltage(
    soc=cell_used.soc, 
    current=3.7,  # Example current value (should be discharge)
    ocv_lookup=cell_used.ocv_lookup, 
    internal_resistance=cell_used.internal_resistance
)

print(f"Final Voltage: {final_voltage:.3f}V")
