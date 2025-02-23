import pybamm

class BatteryModel:
    # Define available battery chemistries
    CHEMISTRY_PARAMETERS = {
        "NMC": pybamm.ParameterValues("Chen2020"),  # NMC battery parameters
        "LFP": pybamm.ParameterValues("Marquis2019"),  # LFP parameters
        "NCA": pybamm.ParameterValues("Ecker2015"),  # NCA parameters
    }

    def __init__(self, model_type="SPM", chemistry="NMC"):
        """Initialize a battery model using PyBaMM"""
        self.chemistry = chemistry
        self.parameter_values = self.CHEMISTRY_PARAMETERS.get(chemistry, pybamm.ParameterValues("Chen2020"))  # Default to NMC
        
        # Define model based on user input
        model_classes = {
            "SPM": pybamm.lithium_ion.SPM,
            "SPMe": pybamm.lithium_ion.SPMe,
            "DFN": pybamm.lithium_ion.DFN,
        }
        self.model = model_classes.get(model_type, pybamm.lithium_ion.SPM)()  # Default to SPM

        # Attach chemistry parameters to the model
        self.simulation = pybamm.Simulation(self.model, parameter_values=self.parameter_values)

    def run_simulation(self, duration=3600):
        """Run the battery simulation for a given time duration (in seconds)"""
        solution = self.simulation.solve([0, duration])
        return solution

    def get_voltage(self, solution):
        """Extract voltage from the simulation results"""
        return solution["Terminal voltage [V]"].entries


# Example Usage
battery = BatteryModel(model_type="SPMe", chemistry="LFP")
solution = battery.run_simulation(100)
voltage = battery.get_voltage(solution)

print(f"Final voltage: {voltage[-1]:.2f}V")
