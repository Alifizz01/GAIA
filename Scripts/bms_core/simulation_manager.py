import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bms_core.battery_model import BatteryModel

class SimulatorManager:
    def __init__(self, model_type="SPM", chemistry="NMC"):
        """Initialize the simulator with the selected battery model."""
        self.battery_model = BatteryModel(model_type, chemistry)
        self.time_data = []
        self.voltage_data = []

    def run_battery_simulation(self, duration=10000):
        """
        Runs the battery simulation and stores the time series data.
        - duration: Simulation time in seconds
        """
        # Generate a time array for every second
        self.time_data = np.arange(0, duration, 1)

        # Run the battery simulation
        solution = self.battery_model.run_simulation(duration)

        # Retrieve resampled voltage data
        self.voltage_data = self.battery_model.get_voltage(solution, self.time_data)

    def get_simulation_results(self):
        """Returns the stored time series and voltage data."""
        return self.time_data, self.voltage_data
