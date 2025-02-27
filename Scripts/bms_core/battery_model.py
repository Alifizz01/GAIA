import numpy as np
import pybamm

class BatteryModel:
    CHEMISTRY_PARAMETERS = {
        "NMC": pybamm.ParameterValues("Chen2020"),
        "LFP": pybamm.ParameterValues("Marquis2019"),
        "NCA": pybamm.ParameterValues("Ecker2015"),
    }

    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15, simulation_mode="Manual Parameter Mode", experiment=None):
        self.chemistry = chemistry
        self.model_type = model_type
        self.parameter_values = self.CHEMISTRY_PARAMETERS.get(chemistry, pybamm.ParameterValues("Chen2020")).copy()
        self.parameter_values.update({"Initial temperature [K]": float(initial_temperature)})
        self.simulation_mode = simulation_mode
        self.experiment = experiment

        # Initialize model and simulation
        self._setup_model_and_simulation()

    def _setup_model_and_simulation(self):
        model_classes = {
            "SPM": pybamm.lithium_ion.SPM,
            "SPMe": pybamm.lithium_ion.SPMe,
            "DFN": pybamm.lithium_ion.DFN,
        }
        self.model = model_classes.get(self.model_type, pybamm.lithium_ion.SPM)()

        if self.simulation_mode == "Experiment Mode" and self.experiment:
            self.simulation = pybamm.Simulation(self.model, 
                                                parameter_values=self.parameter_values, 
                                                experiment=self.experiment)
        else:
            self.simulation = pybamm.Simulation(self.model, parameter_values=self.parameter_values)

    def change_parameters(self, parameter_name, value):
        """Update any battery parameter and rebuild the simulation."""
        self.parameter_values.update({parameter_name: value})
        self._setup_model_and_simulation()

    def run_simulation(self, duration=3600):
        """Run simulation with the latest parameters."""
        solution = self.simulation.solve([0, duration])
        return solution
    
    def get_voltage(self, solution, time_data):
        """Extract voltage and resample it to match `time_data`."""
        original_time = solution["Time [s]"].entries
        original_voltage = solution["Terminal voltage [V]"].entries
        return np.interp(time_data, original_time, original_voltage)
    
    def get_soc(self, solution, time_data):        
        V_100 = self.parameter_values["Open-circuit voltage at 100% SOC [V]"]
        V_0 = self.parameter_values["Open-circuit voltage at 0% SOC [V]"]
        original_time = solution["Time [s]"].entries
        original_voltage = solution["Terminal voltage [V]"].entries
        original_soc = ((original_voltage - V_0) / (V_100 - V_0)) * 100
        return np.clip(np.interp(time_data, original_time, original_soc), 0, 100)

    def get_temperature(self, solution, time_data):
        """Extract and interpolate battery temperature from PyBaMM solution."""
        if "Volume-averaged cell temperature [K]" in solution.keys():
            original_time = solution["Time [s]"].entries
            original_temperature = solution["Volume-averaged cell temperature [K]"].entries
            return np.interp(time_data, original_time, original_temperature)
        else:
            print("Warning: No temperature data found in simulation results.")
            return np.full_like(time_data, 298.15)  # Default 25°C

    def get_current(self, solution, time_data):
        """Extract current data from PyBaMM solution."""
        original_time = solution["Time [s]"].entries
        original_current = solution["Current [A]"].entries
        return np.interp(time_data, original_time, original_current)
