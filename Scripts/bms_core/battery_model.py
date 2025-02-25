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
        
        # Try to get temperature from PyBaMM solution
        try:
            original_temperature = solution["Cell temperature [K]"].entries  # Prefer cell temp over ambient temp
        except KeyError:
            # Fallback to ambient temperature if cell temperature isn't available
            original_temperature = solution["Ambient temperature [K]"].entries
        
        # Interpolate temperature values to match `time_data`
        interpolated_temperature = np.interp(time_data, original_time, original_temperature)

        # Clamp temperature to prevent unrealistic values (assume 0°C to 100°C range)
        interpolated_temperature = np.clip(interpolated_temperature, 273.15, 373.15)  # Kelvin (0°C to 100°C)

        return interpolated_temperature
