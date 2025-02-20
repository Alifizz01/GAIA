import sys
import os

# Add GAIA directory to Python's search path
sys.path.append(os.path.abspath('../'))

from bms_core.thermal_model import ThermalModel  # type: ignore # Now try importing

def TestThermalModel():
    model = ThermalModel(current = 4)
    temperature = model.update_temperature(25, 3600)
    print(f"Updated Battery Temperature: {temperature:.2f}°C")

TestThermalModel()
