"""
Configuration Management Module for GAIA BMS Framework
Handles loading and managing configuration files for simulations.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Manages configuration for BMS simulations.
    Supports JSON configuration files with validation.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config: Dict[str, Any] = {}
        self.config_file = config_file
        self.default_config = self._get_default_config()
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        else:
            self.config = self.default_config.copy()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "battery": {
                "chemistry": "NMC",
                "model_type": "SPM",
                "nominal_capacity": 50.0,  # Ah
                "nominal_voltage": 3.7,  # V
                "initial_temperature": 298.15,  # K
                "initial_soc": 100.0  # %
            },
            "pack": {
                "cells_in_series": 16,
                "cells_in_parallel": 1,
                "balancing_enabled": True,
                "balancing_method": "passive",
                "balancing_threshold": 0.02  # 2%
            },
            "simulation": {
                "duration": 3600,  # seconds
                "time_step": 1.0,  # seconds
                "simulation_mode": "Manual Parameter Mode",
                "experiment_file": None
            },
            "soc_estimation": {
                "method": "aekf",  # "coulomb_counting", "kalman_filter", "aekf"
                "coulombic_efficiency": 0.98,
                "process_noise": 0.001,
                "measurement_noise": 0.01
            },
            "fault_injection": {
                "enabled": False,
                "scenario": None
            },
            "logging": {
                "enabled": True,
                "log_directory": "logs",
                "log_format": "csv",
                "log_interval": 1.0  # seconds
            },
            "scalability": {
                "parallel_processing": False,
                "max_workers": 4,
                "batch_size": 100,
                "cache_enabled": True
            }
        }
    
    def load_config(self, config_file: str):
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
            
            # Merge with default config (deep merge)
            self.config = self._deep_merge(self.default_config, loaded_config)
            self.config_file = config_file
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
            print("Using default configuration.")
            self.config = self.default_config.copy()
    
    def save_config(self, config_file: Optional[str] = None):
        """
        Save current configuration to JSON file.
        
        Args:
            config_file: Path to save config (uses current if None)
        """
        save_file = config_file or self.config_file
        if not save_file:
            raise ValueError("No configuration file specified for saving")
        
        os.makedirs(os.path.dirname(save_file) if os.path.dirname(save_file) else ".", exist_ok=True)
        
        with open(save_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., "battery.chemistry")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self):
        """
        Validate configuration values.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []  # type: List[str]
        
        # Validate battery config
        chemistry = self.get("battery.chemistry")
        if chemistry not in ["NMC", "LFP", "NCA", "LMO", "LTO"]:
            errors.append(f"Invalid battery chemistry: {chemistry}")
        
        model_type = self.get("battery.model_type")
        if model_type not in ["SPM", "SPMe", "DFN"]:
            errors.append(f"Invalid model type: {model_type}")
        
        # Validate pack config
        cells_series = self.get("pack.cells_in_series")
        cells_parallel = self.get("pack.cells_in_parallel")
        if cells_series < 1 or cells_parallel < 1:
            errors.append("Invalid pack configuration: cells must be >= 1")
        
        # Validate simulation config
        duration = self.get("simulation.duration")
        if duration <= 0:
            errors.append("Simulation duration must be > 0")
        
        # Validate SOC estimation
        soc_method = self.get("soc_estimation.method")
        if soc_method not in ["coulomb_counting", "kalman_filter", "aekf"]:
            errors.append(f"Invalid SOC estimation method: {soc_method}")
        
        return len(errors) == 0, errors
    
    def get_battery_config(self) -> Dict:
        """Get battery configuration."""
        return self.config.get("battery", {})
    
    def get_pack_config(self) -> Dict:
        """Get pack configuration."""
        return self.config.get("pack", {})
    
    def get_simulation_config(self) -> Dict:
        """Get simulation configuration."""
        return self.config.get("simulation", {})


def load_default_config() -> ConfigManager:
    """Load default configuration."""
    return ConfigManager()

