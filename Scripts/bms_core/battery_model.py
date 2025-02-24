import numpy as np
import pybamm

class BatteryModel:
    CHEMISTRY_PARAMETERS = {
        "NMC": pybamm.ParameterValues("Chen2020"),
        "LFP": pybamm.ParameterValues("Marquis2019"),
        "NCA": pybamm.ParameterValues("Ecker2015"),
    }

    def __init__(self, model_type="SPM", chemistry="NMC"):
        """Initialize a battery model using PyBaMM"""
        self.chemistry = chemistry
        self.parameter_values = self.CHEMISTRY_PARAMETERS.get(chemistry, pybamm.ParameterValues("Chen2020"))

        model_classes = {
            "SPM": pybamm.lithium_ion.SPM,
            "SPMe": pybamm.lithium_ion.SPMe,
            "DFN": pybamm.lithium_ion.DFN,
        }
        self.model = model_classes.get(model_type, pybamm.lithium_ion.SPM)()

        self.simulation = pybamm.Simulation(self.model, parameter_values=self.parameter_values)

    def run_simulation(self, duration=3600):
        """Run the battery simulation for a given time duration (in seconds)"""
        solution = self.simulation.solve([0, duration])
        return solution

    def get_voltage(self, solution, time_data):
        """Extract voltage and resample it to match `time_data`"""
        original_time = solution["Time [s]"].entries  # Extract original time points
        original_voltage = solution["Terminal voltage [V]"].entries  # Extract original voltage values

        # Resample voltage values to match `time_data`
        self.sampled_voltage = np.interp(time_data, original_time, original_voltage)
        
        return self.sampled_voltage