"""
Battery Pack Module for GAIA BMS Framework
Handles series-parallel battery pack configurations with cell-level monitoring.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from .battery_model import BatteryModel


@dataclass
class CellState:
    """State of a single battery cell."""
    voltage: float
    soc: float
    temperature: float
    current: float
    soh: float = 100.0  # State of Health (%)
    internal_resistance: float = 0.01
    capacity: float = 1.0  # Ah


class BatteryPack:
    """
    Manages a battery pack with series-parallel cell configurations.
    Supports cell-level monitoring, balancing, and health tracking.
    """
    
    def __init__(self, cells_in_series: int, cells_in_parallel: int, 
                 chemistry: str = "NMC", model_type: str = "SPM",
                 initial_temperature: float = 298.15):
        """
        Initialize a battery pack.
        
        Args:
            cells_in_series: Number of cells connected in series
            cells_in_parallel: Number of cells connected in parallel
            chemistry: Battery chemistry (NMC, LFP, NCA)
            model_type: Battery model type (SPM, SPMe, DFN)
            initial_temperature: Initial temperature in Kelvin
        """
        self.cells_in_series = cells_in_series
        self.cells_in_parallel = cells_in_parallel
        self.total_cells = cells_in_series * cells_in_parallel
        
        # Create battery model for cell-level simulation
        self.cell_model = BatteryModel(model_type, chemistry, initial_temperature)
        
        # Initialize cell states
        self.cells: List[List[CellState]] = []
        self._initialize_cells(initial_temperature)
        
        # Pack-level parameters
        self.nominal_voltage_per_cell = 3.7  # V
        self.nominal_capacity_per_cell = 50  # Ah (typical)
        self.pack_voltage = self.nominal_voltage_per_cell * cells_in_series
        self.pack_capacity = self.nominal_capacity_per_cell * cells_in_parallel
        
        # Balancing parameters
        self.balancing_enabled = False
        self.balancing_threshold = 0.02  # 2% SOC difference threshold
        
    def _initialize_cells(self, initial_temperature: float):
        """Initialize all cells in the pack with default states."""
        self.cells = []
        for _ in range(self.cells_in_series):
            parallel_cells = []
            for _ in range(self.cells_in_parallel):
                parallel_cells.append(CellState(
                    voltage=self.nominal_voltage_per_cell,
                    soc=100.0,
                    temperature=initial_temperature,
                    current=0.0
                ))
            self.cells.append(parallel_cells)
    
    def update_cell_state(self, series_idx: int, parallel_idx: int, 
                         voltage: float, soc: float, temperature: float, 
                         current: float, soh: Optional[float] = None):
        """Update state of a specific cell."""
        if 0 <= series_idx < self.cells_in_series and 0 <= parallel_idx < self.cells_in_parallel:
            cell = self.cells[series_idx][parallel_idx]
            cell.voltage = voltage
            cell.soc = soc
            cell.temperature = temperature
            cell.current = current
            if soh is not None:
                cell.soh = soh
    
    def get_pack_voltage(self) -> float:
        """Calculate total pack voltage (sum of series cells)."""
        pack_voltage = 0.0
        for series_group in self.cells:
            # Average voltage of parallel cells, then sum series
            avg_voltage = np.mean([cell.voltage for cell in series_group])
            pack_voltage += avg_voltage
        return pack_voltage
    
    def get_pack_current(self) -> float:
        """Calculate total pack current (sum of parallel branches)."""
        if self.cells_in_series > 0 and len(self.cells[0]) > 0:
            # Current is the same for all series cells in a branch
            return self.cells[0][0].current * self.cells_in_parallel
        return 0.0
    
    def get_pack_soc(self) -> float:
        """Calculate average pack SOC."""
        total_soc = 0.0
        cell_count = 0
        for series_group in self.cells:
            for cell in series_group:
                total_soc += cell.soc
                cell_count += 1
        return total_soc / cell_count if cell_count > 0 else 0.0
    
    def get_pack_soh(self) -> float:
        """Calculate average pack SOH."""
        total_soh = 0.0
        cell_count = 0
        for series_group in self.cells:
            for cell in series_group:
                total_soh += cell.soh
                cell_count += 1
        return total_soh / cell_count if cell_count > 0 else 100.0
    
    def get_cell_imbalance(self) -> Dict[str, float]:
        """
        Analyze cell imbalance in the pack.
        
        Returns:
            Dictionary with imbalance metrics (max_soc_diff, min_voltage, max_voltage, etc.)
        """
        all_socs = [cell.soc for series_group in self.cells for cell in series_group]
        all_voltages = [cell.voltage for series_group in self.cells for cell in series_group]
        all_temps = [cell.temperature for series_group in self.cells for cell in series_group]
        
        return {
            "max_soc_diff": max(all_socs) - min(all_socs) if all_socs else 0.0,
            "min_soc": min(all_socs) if all_socs else 0.0,
            "max_soc": max(all_socs) if all_socs else 0.0,
            "avg_soc": np.mean(all_socs) if all_socs else 0.0,
            "min_voltage": min(all_voltages) if all_voltages else 0.0,
            "max_voltage": max(all_voltages) if all_voltages else 0.0,
            "voltage_std": np.std(all_voltages) if all_voltages else 0.0,
            "min_temperature": min(all_temps) if all_temps else 0.0,
            "max_temperature": max(all_temps) if all_temps else 0.0,
            "temperature_std": np.std(all_temps) if all_temps else 0.0
        }
    
    def detect_faulty_cells(self, voltage_threshold: float = 0.5, 
                           temp_threshold: float = 60.0) -> List[Tuple[int, int]]:
        """
        Detect faulty cells based on voltage and temperature thresholds.
        
        Returns:
            List of (series_idx, parallel_idx) tuples for faulty cells
        """
        faulty_cells = []
        avg_voltage = np.mean([cell.voltage for series_group in self.cells for cell in series_group])
        
        for s_idx, series_group in enumerate(self.cells):
            for p_idx, cell in enumerate(series_group):
                # Check for over/under voltage
                if abs(cell.voltage - avg_voltage) > voltage_threshold:
                    faulty_cells.append((s_idx, p_idx))
                # Check for overtemperature
                elif cell.temperature > temp_threshold + 273.15:  # Convert to Kelvin
                    faulty_cells.append((s_idx, p_idx))
        
        return faulty_cells
    
    def get_pack_statistics(self) -> Dict:
        """Get comprehensive pack statistics."""
        imbalance = self.get_cell_imbalance()
        return {
            "pack_voltage": self.get_pack_voltage(),
            "pack_current": self.get_pack_current(),
            "pack_soc": self.get_pack_soc(),
            "pack_soh": self.get_pack_soh(),
            "pack_power": self.get_pack_voltage() * self.get_pack_current(),
            "configuration": f"{self.cells_in_series}s{self.cells_in_parallel}p",
            "total_cells": self.total_cells,
            "imbalance": imbalance,
            "faulty_cells": len(self.detect_faulty_cells())
        }

