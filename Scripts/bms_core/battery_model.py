<<<<<<< HEAD
import numpy as np
import pybamm

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

    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15, simulation_mode="Manual Parameter Mode", experiment=None):
        self.chemistry = chemistry
        self.model_type = model_type
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
        try:
            original_time = solution["Time [s]"].entries
            original_voltage = solution["Terminal voltage [V]"].entries
            return np.interp(time_data, original_time, original_voltage)
        except KeyError as e:
            raise KeyError(f"Required solution variable not found: {e}. Make sure the simulation completed successfully.")
    
    def get_soc(self, solution, time_data):        
        original_time = solution["Time [s]"].entries
        
        # Try to get SOC directly from solution (preferred method)
        try:
            if "State of Charge" in solution:
                original_soc = solution["State of Charge"].entries * 100  # Convert from fraction to percentage
            elif "SoC" in solution:
                original_soc = solution["SoC"].entries * 100
            else:
                raise KeyError("SOC not directly available in solution")
        except (KeyError, AttributeError):
            # Fallback: Calculate SOC from voltage and OCV parameters
            try:
                V_100 = self.parameter_values["Open-circuit voltage at 100% SOC [V]"]
                V_0 = self.parameter_values["Open-circuit voltage at 0% SOC [V]"]
                original_voltage = solution["Terminal voltage [V]"].entries
                original_soc = ((original_voltage - V_0) / (V_100 - V_0)) * 100
            except KeyError:
                # If parameters don't exist, use a simple linear approximation
                # This is a fallback and may not be accurate
                print("Warning: SOC calculation using fallback method. Results may not be accurate.")
                original_voltage = solution["Terminal voltage [V]"].entries
                v_min, v_max = original_voltage.min(), original_voltage.max()
                original_soc = ((original_voltage - v_min) / (v_max - v_min)) * 100
        
        return np.clip(np.interp(time_data, original_time, original_soc), 0, 100)

    def get_temperature(self, solution, time_data):
        """Extract temperature and resample it to match `time_data`."""
        try:
            original_time = solution["Time [s]"].entries
            # Try volume-averaged temperature first, fallback to other temperature variables
            if "Volume-averaged cell temperature [K]" in solution:
                original_temperature = solution["Volume-averaged cell temperature [K]"].entries
            elif "Cell temperature [K]" in solution:
                original_temperature = solution["Cell temperature [K]"].entries
            else:
                # If temperature is not available, return initial temperature as constant
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
=======
import numpy as np
import pybamm

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

    def __init__(self, model_type="SPM", chemistry="NMC", initial_temperature=298.15, simulation_mode="Manual Parameter Mode", experiment=None):
        self.chemistry = chemistry
        self.model_type = model_type
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
        try:
            original_time = solution["Time [s]"].entries
            original_voltage = solution["Terminal voltage [V]"].entries
            return np.interp(time_data, original_time, original_voltage)
        except KeyError as e:
            raise KeyError(f"Required solution variable not found: {e}. Make sure the simulation completed successfully.")
    
    def get_soc(self, solution, time_data):        
        original_time = solution["Time [s]"].entries
        
        # Try to get SOC directly from solution (preferred method)
        try:
            if "State of Charge" in solution:
                original_soc = solution["State of Charge"].entries * 100  # Convert from fraction to percentage
            elif "SoC" in solution:
                original_soc = solution["SoC"].entries * 100
            else:
                raise KeyError("SOC not directly available in solution")
        except (KeyError, AttributeError):
            # Fallback: Calculate SOC from voltage and OCV parameters
            try:
                V_100 = self.parameter_values["Open-circuit voltage at 100% SOC [V]"]
                V_0 = self.parameter_values["Open-circuit voltage at 0% SOC [V]"]
                original_voltage = solution["Terminal voltage [V]"].entries
                original_soc = ((original_voltage - V_0) / (V_100 - V_0)) * 100
            except KeyError:
                # If parameters don't exist, use a simple linear approximation
                # This is a fallback and may not be accurate
                print("Warning: SOC calculation using fallback method. Results may not be accurate.")
                original_voltage = solution["Terminal voltage [V]"].entries
                v_min, v_max = original_voltage.min(), original_voltage.max()
                original_soc = ((original_voltage - v_min) / (v_max - v_min)) * 100
        
        return np.clip(np.interp(time_data, original_time, original_soc), 0, 100)

    def get_temperature(self, solution, time_data):
        """Extract temperature and resample it to match `time_data`."""
        try:
            original_time = solution["Time [s]"].entries
            # Try volume-averaged temperature first, fallback to other temperature variables
            if "Volume-averaged cell temperature [K]" in solution:
                original_temperature = solution["Volume-averaged cell temperature [K]"].entries
            elif "Cell temperature [K]" in solution:
                original_temperature = solution["Cell temperature [K]"].entries
            else:
                # If temperature is not available, return initial temperature as constant
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
>>>>>>> e25e88bc9d309c3e29a000420b6d5c43e3c84787
