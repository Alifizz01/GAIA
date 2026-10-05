import numpy as np
import pybamm


def _entries(solution, *names):
    """First of `names` the solution provides, or None.

    `name in solution` does not work: PyBaMM's Solution has no __contains__,
    so Python falls back to iterating it and raises TypeError.
    """
    for name in names:
        try:
            return solution[name].entries
        except KeyError:
            continue
    return None

class BatteryModel:
    # Parameter set names for different chemistries (ordered by likelihood of availability)
    # Using lazy initialization to handle cases where parameter sets might not be available
    CHEMISTRY_PARAMETER_SETS = {
        "NMC": ["Ai2020", "Chen2020", "Chen2020_composite", "Chen2020_composite_NMC", "NCA_Kim2011"],
        "LFP": ["Marquis2019", "Prada2013", "Ai2020", "Chen2020"],
        "NCA": ["NCA_Kim2011", "Ecker2015", "Ai2020", "Chen2020"],
        "LMO": ["Ai2020", "Chen2020"],
        "LTO": ["Ai2020", "Chen2020"],
    }

    @staticmethod
    def _get_available_parameter_sets():
        """Try to discover available parameter sets in PyBaMM."""
        available = []
        # Common PyBaMM parameter set names to try (most common first)
        common_sets = [
            "Ai2020",
            "Marquis2019",
            "Prada2013",
            "Chen2020",
            "Chen2020_composite",
            "Chen2020_composite_LCO",
            "Chen2020_composite_NMC",
            "Ecker2015",
            "NCA_Kim2011",
            "OKane2022",
            "Ramadass2004"
        ]
        for name in common_sets:
            try:
                test_params = pybamm.ParameterValues(name)
                available.append(name)
            except (FileNotFoundError, KeyError, ValueError, AttributeError):
                pass
        return available

    @staticmethod
    def _get_parameter_values(chemistry: str):
        """
        Get parameter values for a chemistry, trying multiple parameter set names.

        Args:
            chemistry: Battery chemistry name

        Returns:
            ParameterValues object
        """
        parameter_sets = BatteryModel.CHEMISTRY_PARAMETER_SETS.get(
            chemistry,
            ["Ai2020", "Chen2020", "Prada2013", "Marquis2019"]
        )

        last_error = None
        for param_set_name in parameter_sets:
            try:
                param_values = pybamm.ParameterValues(param_set_name)
                print(f"Loaded parameter set '{param_set_name}' for {chemistry} chemistry")
                return param_values
            except (FileNotFoundError, KeyError, ValueError, AttributeError) as e:
                last_error = e
                continue

        # If all parameter sets failed, try to find any available parameter set
        available_sets = BatteryModel._get_available_parameter_sets()
        if available_sets:
            print(f"Warning: Chemistry-specific parameter set not found for '{chemistry}'. "
                  f"Using '{available_sets[0]}' as fallback.")
            try:
                return pybamm.ParameterValues(available_sets[0])
            except Exception as e:
                last_error = e

        # If still no parameter sets found, provide helpful error message
        print("\n" + "="*70)
        print("ERROR: Could not find any PyBaMM parameter sets")
        print("="*70)
        print(f"Chemistry requested: {chemistry}")
        print(f"Tried parameter sets: {parameter_sets}")
        print(f"Available parameter sets found: {available_sets if available_sets else 'None'}")
        print("\nThis usually means PyBaMM parameter files are missing.")
        print("\nQUICK FIX:")
        print("  Run this script to attempt automatic fix:")
        print("  python fix_pybamm_params.py")
        print("\nMANUAL SOLUTIONS:")
        print("1. Use Python 3.12: python3.12 -m pip install pybamm")
        print("2. Reinstall PyBaMM: pip uninstall pybamm && pip install pybamm")
        print("3. Install with all extras: pip install pybamm[all]")
        print("4. Check PyBaMM: python -c \"import pybamm; print(pybamm.__version__)\"")
        print("\nSee INSTALL_PYBAMM_PARAMS.md for detailed instructions.")
        print("="*70 + "\n")

        error_msg = (
            f"Could not find any PyBaMM parameter sets for chemistry '{chemistry}'. "
            f"Tried: {parameter_sets}. "
            f"Available: {available_sets if available_sets else 'None'}. "
            f"Please install PyBaMM parameter sets. See INSTALL_PYBAMM_PARAMS.md for help."
        )
        raise RuntimeError(error_msg)

    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15, simulation_mode="Manual Parameter Mode",
                 experiment=None, thermal="isothermal"):
        """thermal: "isothermal" (constant temperature, the PyBaMM default) or
        "lumped" (one heat balance for the whole cell, so temperature rises
        with current and cools to ambient)."""
        self.chemistry = chemistry
        self.model_type = model_type
        self.thermal = thermal
        self.parameter_values = self._get_parameter_values(chemistry).copy()
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
        options = {} if self.thermal == "isothermal" else {"thermal": self.thermal}
        self.model = model_classes.get(self.model_type, pybamm.lithium_ion.SPM)(options)

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
        # Ask for a dense output grid. With only [0, duration] the solver
        # returns its own few steps and every curve between them is a
        # straight line. (t_interp needs PyBaMM >= 24.5; older versions
        # take the grid as t_eval.)
        grid = np.linspace(0, duration, max(200, min(int(duration) + 1, 2000)))
        try:
            solution = self.simulation.solve([0, duration], t_interp=grid)
        except TypeError:
            solution = self.simulation.solve(grid)
        return solution

    def get_voltage(self, solution, time_data):
        """Extract voltage and resample it to match `time_data`."""
        try:
            original_time = solution["Time [s]"].entries
            original_voltage = _entries(solution, "Voltage [V]", "Terminal voltage [V]")
            if original_voltage is None:
                raise KeyError("Voltage [V]")
            return np.interp(time_data, original_time, original_voltage)
        except KeyError as e:
            raise KeyError(f"Required solution variable not found: {e}. Make sure the simulation completed successfully.")

    def get_soc(self, solution, time_data):
        original_time = solution["Time [s]"].entries

        # Preferred: SOC from the charge actually drawn, which PyBaMM tracks
        # exactly. Starts from the initial SOC (100 % unless configured).
        original_soc = _entries(solution, "State of Charge", "SoC")
        if original_soc is not None:
            original_soc = original_soc * 100
        else:
            drawn = _entries(solution, "Discharge capacity [A.h]")
            nominal = self.parameter_values.get("Nominal cell capacity [A.h]")
            if drawn is not None and nominal:
                original_soc = 100.0 * (1.0 - drawn / nominal)
            else:
                # Last resort, and not accurate: stretch the voltage range.
                print("Warning: SOC calculation using fallback method. Results may not be accurate.")
                original_voltage = _entries(solution, "Voltage [V]", "Terminal voltage [V]")
                v_min, v_max = original_voltage.min(), original_voltage.max()
                original_soc = ((original_voltage - v_min) / (v_max - v_min)) * 100

        return np.clip(np.interp(time_data, original_time, original_soc), 0, 100)

    def get_temperature(self, solution, time_data):
        """Extract temperature and resample it to match `time_data`."""
        try:
            original_time = solution["Time [s]"].entries
            original_temperature = _entries(solution, "Volume-averaged cell temperature [K]", "Cell temperature [K]")
            if original_temperature is None:
                print("Warning: Temperature data not available in solution. Using initial temperature.")
                return np.full_like(time_data, self.parameter_values["Initial temperature [K]"])
            return np.interp(time_data, original_time, original_temperature)
        except KeyError as e:
            print(f"Warning: Temperature extraction failed: {e}. Using initial temperature.")
            return np.full_like(time_data, self.parameter_values.get("Initial temperature [K]", 298.15))

    def get_current(self, solution, time_data):
        """Extract current data from PyBaMM solution."""
        try:
            original_time = solution["Time [s]"].entries
            original_current = solution["Current [A]"].entries
            return np.interp(time_data, original_time, original_current)
        except KeyError as e:
            raise KeyError(f"Required solution variable not found: {e}. Make sure the simulation completed successfully.")
