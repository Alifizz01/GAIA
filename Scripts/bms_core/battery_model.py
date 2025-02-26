import numpy as np
import pybamm

class BatteryModel:
    CHEMISTRY_PARAMETERS = {
        "NMC": pybamm.ParameterValues("Chen2020"),
        "LFP": pybamm.ParameterValues("Marquis2019"),
        "NCA": pybamm.ParameterValues("Ecker2015"),
    }

    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15):
        self.chemistry = chemistry
        self.model_type = model_type
        self.parameter_values = self.CHEMISTRY_PARAMETERS.get(chemistry, pybamm.ParameterValues("Chen2020")).copy()
        self.parameter_values.update({"Initial temperature [K]": float(initial_temperature)})
        self._setup_model_and_simulation()  # Initialize model/simulation

    def _setup_model_and_simulation(self):
        """Recreate model and simulation with current parameters."""
        model_classes = {
            "SPM": pybamm.lithium_ion.SPM,
            "SPMe": pybamm.lithium_ion.SPMe,
            "DFN": pybamm.lithium_ion.DFN,
        }
        self.model = model_classes.get(self.model_type, pybamm.lithium_ion.SPM)()
        self.simulation = pybamm.Simulation(self.model, parameter_values=self.parameter_values)

    def change_temperature(self, new_temperature):
        """Update temperature and rebuild model/simulation."""
        self.parameter_values.update({"Initial temperature [K]": new_temperature})
        self._setup_model_and_simulation()  # Reinitialize after parameter change

    def run_simulation(self, duration=3600):
        """Run simulation with the latest parameters."""
        solution = self.simulation.solve([0, duration])
        return solution
    
    def get_voltage(self, solution, time_data):
        """Extract voltage and resample it to match `time_data`"""
        original_time = solution["Time [s]"].entries  # Extract original time points
        original_voltage = solution["Terminal voltage [V]"].entries  # Extract original voltage values

        # Resample voltage values to match `time_data`
        sampled_voltage = np.interp(time_data, original_time, original_voltage)
        
        return sampled_voltage
    
    def get_soc(self, solution, time_data):        
        # Extract fixed max/min voltage from parameter values
        V_100 = self.parameter_values["Open-circuit voltage at 100% SOC [V]"]
        V_0 = self.parameter_values["Open-circuit voltage at 0% SOC [V]"]

        # Extract terminal voltage from PyBaMM solution
        original_time = solution["Time [s]"].entries  # Simulation time points
        original_voltage = solution["Terminal voltage [V]"].entries  # Voltage output

        # Compute SOC using linear mapping formula
        original_soc = ((original_voltage - V_0) / (V_100 - V_0)) * 100

        # Interpolate SOC values to match `time_data`
        soc = np.interp(time_data, original_time, original_soc)

        # Ensure SOC is within valid range (0% to 100%)
        soc = np.clip(soc, 0, 100)

        return soc

    def get_temperature(self, solution, time_data):
        """Extract and interpolate battery temperature from PyBaMM solution."""
        
        original_time = solution["Time [s]"].entries  # Simulation time points
        original_temperature = solution["Volume-averaged cell temperature [K]"].entries
        
        # Interpolate temperature values to match `time_data`
        interpolated_temperature = np.interp(time_data, original_time, original_temperature)

        return interpolated_temperature

    def get_current(self, solution, time_data):

        original_time = solution["Time [s]"].entries  # Simulation time points
        original_current = solution["Current [A]"].entries

        sampled_current = np.interp(time_data, original_time, original_current)

        return sampled_current
