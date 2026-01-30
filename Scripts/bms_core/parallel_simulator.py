<<<<<<< HEAD
"""
Parallel Simulation Module for GAIA BMS Framework
Enables parallel processing of multiple simulations for scalability.
"""

from typing import List, Dict, Callable, Optional
from joblib import Parallel, delayed
import numpy as np
from .simulation_manager import SimulatorManager


class ParallelSimulator:
    """
    Handles parallel execution of multiple battery simulations.
    Enables batch processing and parameter sweeps.
    """
    
    def __init__(self, n_jobs: int = -1, backend: str = "threading"):
        """
        Initialize parallel simulator.
        
        Args:
            n_jobs: Number of parallel jobs (-1 for all cores)
            backend: Backend for parallel processing ("threading" or "multiprocessing")
        """
        self.n_jobs = n_jobs
        self.backend = backend
    
    def run_batch_simulations(self, 
                             simulation_configs: List[Dict],
                             simulation_func: Optional[Callable] = None) -> List[Dict]:
        """
        Run multiple simulations in parallel.
        
        Args:
            simulation_configs: List of simulation configuration dictionaries
            simulation_func: Optional custom simulation function
            
        Returns:
            List of simulation results
        """
        if simulation_func is None:
            simulation_func = self._default_simulation_function
        
        results = Parallel(n_jobs=self.n_jobs, backend=self.backend)(
            delayed(simulation_func)(config) for config in simulation_configs
        )
        
        return results
    
    def _default_simulation_function(self, config: Dict) -> Dict:
        """
        Default simulation function.
        
        Args:
            config: Simulation configuration dictionary
            
        Returns:
            Simulation results dictionary
        """
        try:
            sim_manager = SimulatorManager(
                model_type=config.get("model_type", "SPM"),
                chemistry=config.get("chemistry", "NMC"),
                initial_temperature=config.get("initial_temperature", 298.15)
            )
            
            duration = config.get("duration", 3600)
            sim_manager.run_battery_simulation(duration)
            
            time_data, voltage_data, soc_data, temp_data, current_data = \
                sim_manager.get_simulation_results()
            
            return {
                "config": config,
                "success": True,
                "time": time_data,
                "voltage": voltage_data,
                "soc": soc_data,
                "temperature": temp_data,
                "current": current_data
            }
        except Exception as e:
            return {
                "config": config,
                "success": False,
                "error": str(e)
            }
    
    def parameter_sweep(self, 
                       base_config: Dict,
                       parameter_name: str,
                       parameter_values: List) -> List[Dict]:
        """
        Perform a parameter sweep across multiple values.
        
        Args:
            base_config: Base simulation configuration
            parameter_name: Name of parameter to vary (e.g., "chemistry", "model_type")
            parameter_values: List of values to sweep
            
        Returns:
            List of simulation results for each parameter value
        """
        configs = []
        for value in parameter_values:
            config = base_config.copy()
            config[parameter_name] = value
            configs.append(config)
        
        return self.run_batch_simulations(configs)
    
    def multi_parameter_sweep(self, 
                             base_config: Dict,
                             parameters: Dict[str, List]) -> List[Dict]:
        """
        Perform a multi-parameter sweep (factorial design).
        
        Args:
            base_config: Base simulation configuration
            parameters: Dictionary mapping parameter names to value lists
            
        Returns:
            List of simulation results
        """
        import itertools
        
        # Generate all combinations
        param_names = list(parameters.keys())
        param_values = list(parameters.values())
        combinations = list(itertools.product(*param_values))
        
        configs = []
        for combo in combinations:
            config = base_config.copy()
            for name, value in zip(param_names, combo):
                config[name] = value
            configs.append(config)
        
        return self.run_batch_simulations(configs)

=======
"""
Parallel Simulation Module for GAIA BMS Framework
Enables parallel processing of multiple simulations for scalability.
"""

from typing import List, Dict, Callable, Optional
from joblib import Parallel, delayed
import numpy as np
from .simulation_manager import SimulatorManager


class ParallelSimulator:
    """
    Handles parallel execution of multiple battery simulations.
    Enables batch processing and parameter sweeps.
    """
    
    def __init__(self, n_jobs: int = -1, backend: str = "threading"):
        """
        Initialize parallel simulator.
        
        Args:
            n_jobs: Number of parallel jobs (-1 for all cores)
            backend: Backend for parallel processing ("threading" or "multiprocessing")
        """
        self.n_jobs = n_jobs
        self.backend = backend
    
    def run_batch_simulations(self, 
                             simulation_configs: List[Dict],
                             simulation_func: Optional[Callable] = None) -> List[Dict]:
        """
        Run multiple simulations in parallel.
        
        Args:
            simulation_configs: List of simulation configuration dictionaries
            simulation_func: Optional custom simulation function
            
        Returns:
            List of simulation results
        """
        if simulation_func is None:
            simulation_func = self._default_simulation_function
        
        results = Parallel(n_jobs=self.n_jobs, backend=self.backend)(
            delayed(simulation_func)(config) for config in simulation_configs
        )
        
        return results
    
    def _default_simulation_function(self, config: Dict) -> Dict:
        """
        Default simulation function.
        
        Args:
            config: Simulation configuration dictionary
            
        Returns:
            Simulation results dictionary
        """
        try:
            sim_manager = SimulatorManager(
                model_type=config.get("model_type", "SPM"),
                chemistry=config.get("chemistry", "NMC"),
                initial_temperature=config.get("initial_temperature", 298.15)
            )
            
            duration = config.get("duration", 3600)
            sim_manager.run_battery_simulation(duration)
            
            time_data, voltage_data, soc_data, temp_data, current_data = \
                sim_manager.get_simulation_results()
            
            return {
                "config": config,
                "success": True,
                "time": time_data,
                "voltage": voltage_data,
                "soc": soc_data,
                "temperature": temp_data,
                "current": current_data
            }
        except Exception as e:
            return {
                "config": config,
                "success": False,
                "error": str(e)
            }
    
    def parameter_sweep(self, 
                       base_config: Dict,
                       parameter_name: str,
                       parameter_values: List) -> List[Dict]:
        """
        Perform a parameter sweep across multiple values.
        
        Args:
            base_config: Base simulation configuration
            parameter_name: Name of parameter to vary (e.g., "chemistry", "model_type")
            parameter_values: List of values to sweep
            
        Returns:
            List of simulation results for each parameter value
        """
        configs = []
        for value in parameter_values:
            config = base_config.copy()
            config[parameter_name] = value
            configs.append(config)
        
        return self.run_batch_simulations(configs)
    
    def multi_parameter_sweep(self, 
                             base_config: Dict,
                             parameters: Dict[str, List]) -> List[Dict]:
        """
        Perform a multi-parameter sweep (factorial design).
        
        Args:
            base_config: Base simulation configuration
            parameters: Dictionary mapping parameter names to value lists
            
        Returns:
            List of simulation results
        """
        import itertools
        
        # Generate all combinations
        param_names = list(parameters.keys())
        param_values = list(parameters.values())
        combinations = list(itertools.product(*param_values))
        
        configs = []
        for combo in combinations:
            config = base_config.copy()
            for name, value in zip(param_names, combo):
                config[name] = value
            configs.append(config)
        
        return self.run_batch_simulations(configs)

>>>>>>> e25e88bc9d309c3e29a000420b6d5c43e3c84787
