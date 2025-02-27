import numpy as np
import sys
import os
import pybamm
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from bms_core.battery_model import BatteryModel

class SimulatorManager:
    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15):
        """Initialize the simulator with the selected battery model."""
        self.battery_model = BatteryModel(model_type, chemistry, initial_temperature)
        self.time_data = []
        self.voltage_data = []
        self.soc_data = []
        self.temperature_data = []
        self.current_data = []

        # Define a test profile directory and ensure it exists
        self.test_profile_directory = os.path.join(os.path.dirname(__file__), "../tests/")
        os.makedirs(self.test_profile_directory, exist_ok=True)

    def run_battery_simulation(self, duration=10000):
        """Runs the battery simulation and stores the time series data."""
        self.time_data = np.arange(0, duration, 1)
        solution = self.battery_model.run_simulation(duration)
        self.voltage_data = self.battery_model.get_voltage(solution, self.time_data)
        self.soc_data = self.battery_model.get_soc(solution, self.time_data)
        self.temperature_data = self.battery_model.get_temperature(solution, self.time_data)
        self.current_data = self.battery_model.get_current(solution, self.time_data)

    def get_simulation_results(self):
        """Returns the stored time series and voltage data."""
        return self.time_data, self.voltage_data, self.soc_data, self.temperature_data, self.current_data
    
    def update_parameters(self, parameter_name, new_value):
        """Update battery model parameters dynamically."""
        self.battery_model.change_parameters(parameter_name, new_value)


    def load_experiment(self, filename="test_profile.json"):
        """Loads an experiment profile from a JSON file and runs it in PyBaMM."""
        file_path = os.path.join(self.test_profile_directory, filename)

        if not os.path.exists(file_path):
            print(f"ERROR: Experiment file not found -> {file_path}")
            return None

        try:
            with open(file_path, "r") as json_file:
                experiment_data = json.load(json_file)
        except Exception as e:
            print(f"ERROR: Failed to load JSON file -> {e}")
            return None

        experiment_steps = experiment_data.get("experiment_steps", [])
        repeat = experiment_data.get("repeat", 1)

        if not experiment_steps:
            print("ERROR: No experiment steps found in JSON file!")
            return None

        # Convert JSON experiment steps to PyBaMM Experiment format
        try:
            experiment = pybamm.Experiment(experiment_steps * repeat)
            print(f"SUCCESS: Experiment loaded -> {experiment_steps}")
        except Exception as e:
            print(f"ERROR: Failed to create PyBaMM Experiment -> {e}")
            return None

        # Update battery model with experiment
        self.battery_model.simulation = pybamm.Simulation(self.battery_model.model, 
                                                        parameter_values=self.battery_model.parameter_values, 
                                                        experiment=experiment)

        self.run_experiment_simulation()
        return True  # Indicate success


    def run_experiment_simulation(self):
        """Runs an experiment simulation and updates stored results."""
        solution = self.battery_model.simulation.solve()

        # Store time-series results
        self.time_data = solution["Time [s]"].entries
        self.voltage_data = solution["Terminal voltage [V]"].entries
        self.soc_data = self.battery_model.get_soc(solution, self.time_data)
        self.temperature_data = self.battery_model.get_temperature(solution, self.time_data)
        self.current_data = self.battery_model.get_current(solution, self.time_data)
