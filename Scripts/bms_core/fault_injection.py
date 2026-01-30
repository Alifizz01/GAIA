"""
Fault Injection Module for GAIA BMS Framework
Enables testing of BMS behavior under various fault conditions.
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class FaultType(Enum):
    """Types of faults that can be injected."""
    CELL_SHORT = "cell_short"
    CELL_OPEN = "cell_open"
    OVERVOLTAGE = "overvoltage"
    UNDERVOLTAGE = "undervoltage"
    OVERCURRENT = "overcurrent"
    OVERTEMPERATURE = "overtemperature"
    INTERNAL_RESISTANCE_INCREASE = "internal_resistance_increase"
    CAPACITY_DEGRADATION = "capacity_degradation"
    THERMAL_RUNAWAY = "thermal_runaway"
    CONNECTION_FAILURE = "connection_failure"


@dataclass
class Fault:
    """Represents a fault condition."""
    fault_type: FaultType
    cell_position: Optional[tuple] = None  # (series_idx, parallel_idx)
    severity: float = 1.0  # 0.0 to 1.0
    start_time: float = 0.0  # Simulation time when fault starts
    duration: Optional[float] = None  # None for permanent faults
    parameters: Dict = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class FaultInjector:
    """
    Handles fault injection and simulation for testing BMS behavior.
    """
    
    def __init__(self):
        """Initialize fault injector."""
        self.active_faults: List[Fault] = []
        self.fault_history: List[Fault] = []
        
        # Default fault parameters
        self.fault_parameters = {
            FaultType.CELL_SHORT: {
                "resistance": 0.01,  # Ohms
                "voltage_drop": 0.5  # V
            },
            FaultType.CELL_OPEN: {
                "resistance": 1e6  # Very high resistance
            },
            FaultType.OVERVOLTAGE: {
                "threshold": 4.3,  # V
                "voltage_increase": 0.1  # V
            },
            FaultType.UNDERVOLTAGE: {
                "threshold": 2.5,  # V
                "voltage_decrease": 0.1  # V
            },
            FaultType.OVERCURRENT: {
                "threshold": 100.0,  # A
                "current_multiplier": 1.5
            },
            FaultType.OVERTEMPERATURE: {
                "threshold": 60.0,  # °C
                "temperature_increase": 10.0  # °C
            },
            FaultType.INTERNAL_RESISTANCE_INCREASE: {
                "resistance_multiplier": 5.0
            },
            FaultType.CAPACITY_DEGRADATION: {
                "capacity_reduction": 0.2  # 20%
            },
            FaultType.THERMAL_RUNAWAY: {
                "temperature_rate": 5.0,  # °C/s
                "critical_temperature": 80.0  # °C
            },
            FaultType.CONNECTION_FAILURE: {
                "resistance": 1e3  # High resistance connection
            }
        }
    
    def inject_fault(self, fault: Fault):
        """
        Inject a fault into the system.
        
        Args:
            fault: Fault object to inject
        """
        fault.parameters = self.fault_parameters.get(fault.fault_type, {})
        self.active_faults.append(fault)
        self.fault_history.append(fault)
        print(f"Fault injected: {fault.fault_type.value} at cell {fault.cell_position}")
    
    def remove_fault(self, fault_type: FaultType, cell_position: Optional[tuple] = None):
        """Remove a specific fault."""
        faults_to_remove = [
            f for f in self.active_faults
            if f.fault_type == fault_type and 
            (cell_position is None or f.cell_position == cell_position)
        ]
        for fault in faults_to_remove:
            self.active_faults.remove(fault)
    
    def clear_all_faults(self):
        """Remove all active faults."""
        self.active_faults.clear()
    
    def apply_faults(self, cell_state: Dict, current_time: float) -> Dict:
        """
        Apply active faults to a cell state.
        
        Args:
            cell_state: Dictionary with cell state (voltage, current, temperature, etc.)
            current_time: Current simulation time
            
        Returns:
            Modified cell state dictionary
        """
        modified_state = cell_state.copy()
        
        # Filter faults that are active at current time
        active_faults_now = [
            f for f in self.active_faults
            if f.start_time <= current_time and
            (f.duration is None or current_time <= f.start_time + f.duration)
        ]
        
        for fault in active_faults_now:
            modified_state = self._apply_single_fault(modified_state, fault, current_time)
        
        return modified_state
    
    def _apply_single_fault(self, state: Dict, fault: Fault, current_time: float) -> Dict:
        """Apply a single fault to the cell state."""
        params = fault.parameters
        severity = fault.severity
        modified_state = state.copy()
        
        if fault.fault_type == FaultType.CELL_SHORT:
            # Reduce voltage due to internal short
            voltage_drop = params.get("voltage_drop", 0.5) * severity
            modified_state["voltage"] = max(0.0, modified_state.get("voltage", 3.7) - voltage_drop)
            modified_state["internal_resistance"] = params.get("resistance", 0.01)
            
        elif fault.fault_type == FaultType.CELL_OPEN:
            # Open circuit - no current flow
            modified_state["current"] = 0.0
            modified_state["internal_resistance"] = params.get("resistance", 1e6)
            
        elif fault.fault_type == FaultType.OVERVOLTAGE:
            # Increase voltage beyond normal limits
            voltage_increase = params.get("voltage_increase", 0.1) * severity
            modified_state["voltage"] = modified_state.get("voltage", 3.7) + voltage_increase
            
        elif fault.fault_type == FaultType.UNDERVOLTAGE:
            # Decrease voltage below normal limits
            voltage_decrease = params.get("voltage_decrease", 0.1) * severity
            modified_state["voltage"] = max(0.0, modified_state.get("voltage", 3.7) - voltage_decrease)
            
        elif fault.fault_type == FaultType.OVERCURRENT:
            # Increase current beyond safe limits
            current_multiplier = 1.0 + (params.get("current_multiplier", 1.5) - 1.0) * severity
            modified_state["current"] = modified_state.get("current", 0.0) * current_multiplier
            
        elif fault.fault_type == FaultType.OVERTEMPERATURE:
            # Increase temperature
            temp_increase = params.get("temperature_increase", 10.0) * severity
            modified_state["temperature"] = modified_state.get("temperature", 298.15) + temp_increase
            
        elif fault.fault_type == FaultType.INTERNAL_RESISTANCE_INCREASE:
            # Increase internal resistance
            resistance_multiplier = 1.0 + (params.get("resistance_multiplier", 5.0) - 1.0) * severity
            modified_state["internal_resistance"] = (
                modified_state.get("internal_resistance", 0.01) * resistance_multiplier
            )
            
        elif fault.fault_type == FaultType.CAPACITY_DEGRADATION:
            # Reduce capacity
            capacity_reduction = params.get("capacity_reduction", 0.2) * severity
            modified_state["capacity"] = modified_state.get("capacity", 1.0) * (1.0 - capacity_reduction)
            
        elif fault.fault_type == FaultType.THERMAL_RUNAWAY:
            # Exponential temperature increase
            elapsed_time = current_time - fault.start_time
            temp_rate = params.get("temperature_rate", 5.0) * severity
            temp_increase = temp_rate * elapsed_time
            modified_state["temperature"] = modified_state.get("temperature", 298.15) + temp_increase
            
            # Critical temperature check
            if modified_state["temperature"] > params.get("critical_temperature", 80.0) + 273.15:
                # Catastrophic failure - cell is destroyed
                modified_state["voltage"] = 0.0
                modified_state["current"] = 0.0
                modified_state["capacity"] = 0.0
                
        elif fault.fault_type == FaultType.CONNECTION_FAILURE:
            # High resistance connection
            modified_state["internal_resistance"] = params.get("resistance", 1e3) * severity
        
        return modified_state
    
    def get_active_faults(self) -> List[Fault]:
        """Get list of currently active faults."""
        return self.active_faults.copy()
    
    def get_fault_statistics(self) -> Dict:
        """Get statistics about injected faults."""
        total_faults = len(self.fault_history)
        active_faults = len(self.active_faults)
        
        fault_types = {}
        for fault in self.fault_history:
            fault_type = fault.fault_type.value
            fault_types[fault_type] = fault_types.get(fault_type, 0) + 1
        
        return {
            "total_faults_injected": total_faults,
            "active_faults": active_faults,
            "fault_types": fault_types
        }
    
    def create_fault_scenario(self, scenario_name: str) -> List[Fault]:
        """
        Create predefined fault scenarios for testing.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            List of faults for the scenario
        """
        scenarios = {
            "single_cell_failure": [
                Fault(FaultType.CELL_SHORT, cell_position=(0, 0), severity=0.5)
            ],
            "thermal_event": [
                Fault(FaultType.OVERTEMPERATURE, severity=0.7),
                Fault(FaultType.THERMAL_RUNAWAY, severity=0.5, start_time=10.0)
            ],
            "voltage_imbalance": [
                Fault(FaultType.OVERVOLTAGE, cell_position=(0, 0), severity=0.3),
                Fault(FaultType.UNDERVOLTAGE, cell_position=(1, 0), severity=0.3)
            ],
            "aging_simulation": [
                Fault(FaultType.CAPACITY_DEGRADATION, severity=0.2),
                Fault(FaultType.INTERNAL_RESISTANCE_INCREASE, severity=0.3)
            ],
            "connection_problems": [
                Fault(FaultType.CONNECTION_FAILURE, cell_position=(0, 0), severity=0.4),
                Fault(FaultType.CONNECTION_FAILURE, cell_position=(1, 0), severity=0.4)
            ]
        }
        
        return scenarios.get(scenario_name, [])

