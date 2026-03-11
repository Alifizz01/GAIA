"""
BMS Controller Core for GAIA BMS Framework
Central controller orchestrating all BMS functions including protection, balancing, and state management.
"""

from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import time
from datetime import datetime

from .hardware_interface import HardwareInterface
from .protection_system import ProtectionSystem, ProtectionLevel, ProtectionFaultType
from .soc_estimation import SOCEstimator, SOCEstimationMethod
from .battery_balancing import BatteryBalancer, BalancingMethod
from .battery_pack import BatteryPack


class BMSState(Enum):
    """BMS system states."""
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    BALANCING = "balancing"
    FAULT = "fault"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


@dataclass
class BMSStatus:
    """BMS system status information."""
    state: BMSState
    pack_voltage: float
    pack_current: float
    pack_soc: float
    pack_soh: float
    pack_temperature: float
    active_faults: List[ProtectionFaultType]
    balancing_active: bool
    charge_enabled: bool
    discharge_enabled: bool
    timestamp: float


class BMSController:
    """
    Main BMS Controller orchestrating all battery management functions.
    
    The controller runs a control loop that:
    1. Reads hardware state via Hardware Interface
    2. Performs protection checks
    3. Estimates SOC/SOH
    4. Controls balancing
    5. Manages system state
    6. Writes control commands
    """
    
    def __init__(self, 
                 hardware_interface: HardwareInterface,
                 pack_config: Dict,
                 bms_config: Optional[Dict] = None):
        """
        Initialize BMS Controller.
        
        Args:
            hardware_interface: Hardware interface (simulation or real)
            pack_config: Pack configuration (cells_in_series, cells_in_parallel, etc.)
            bms_config: BMS configuration (protection thresholds, algorithms, etc.)
        """
        self.hardware = hardware_interface
        self.pack_config = pack_config
        self.bms_config = bms_config or self._get_default_bms_config()
        
        # Initialize components
        self.protection_system = ProtectionSystem(self.bms_config.get("protection", {}))
        self.battery_pack = BatteryPack(
            cells_in_series=pack_config.get("cells_in_series", 1),
            cells_in_parallel=pack_config.get("cells_in_parallel", 1),
            chemistry=pack_config.get("chemistry", "NMC")
        )
        
        # SOC estimation
        soc_method = SOCEstimationMethod[self.bms_config.get("soc_estimation", {}).get("method", "AEKF").upper()]
        self.soc_estimator = SOCEstimator(
            method=soc_method,
            nominal_capacity=pack_config.get("nominal_capacity", 50.0),
            initial_soc=pack_config.get("initial_soc", 100.0)
        )
        
        # Balancing
        balancing_method = BalancingMethod[self.bms_config.get("balancing", {}).get("method", "PASSIVE").upper()]
        self.balancer = BatteryBalancer(
            method=balancing_method,
            balancing_threshold=self.bms_config.get("balancing", {}).get("threshold", 0.02)
        )
        
        # System state
        self.state = BMSState.IDLE
        self.state_history: List[tuple] = []  # (timestamp, state)
        
        # Control flags
        self.charge_enabled = False
        self.discharge_enabled = False
        self.balancing_enabled = self.bms_config.get("balancing", {}).get("enabled", True)
        
        # Status
        self.current_status: Optional[BMSStatus] = None
        self.status_history: List[BMSStatus] = []
        
        # Callbacks
        self.state_change_callbacks: List[Callable] = []
        self.fault_callbacks: List[Callable] = []
        
        # Statistics
        self.cycle_count = 0
        self.total_energy_charged = 0.0  # Wh
        self.total_energy_discharged = 0.0  # Wh
        self.start_time = time.time()
        
        # Control loop
        self.control_loop_running = False
        self.control_loop_frequency = self.bms_config.get("control_loop_frequency", 10.0)  # Hz
        self.last_update_time = 0.0
        
    def _get_default_bms_config(self) -> Dict:
        """Get default BMS configuration."""
        return {
            "protection": {
                "overvoltage_threshold": 4.25,  # V
                "undervoltage_threshold": 2.5,   # V
                "overcurrent_threshold": 100.0,  # A
                "overtemperature_threshold": 60.0,  # °C
                "imbalance_threshold": 0.2  # V
            },
            "soc_estimation": {
                "method": "aekf"
            },
            "balancing": {
                "enabled": True,
                "method": "passive",
                "threshold": 0.02  # 2% SOC difference
            },
            "control_loop_frequency": 10.0  # Hz
        }
    
    def initialize(self) -> bool:
        """Initialize BMS Controller."""
        if not self.hardware.initialize():
            return False
        
        self.state = BMSState.IDLE
        self.charge_enabled = False
        self.discharge_enabled = False
        return True
    
    def close(self):
        """Close BMS Controller and cleanup."""
        self.stop_control_loop()
        self.hardware.close()
        self.state = BMSState.IDLE
    
    def update(self, dt: float):
        """
        Update BMS Controller state (called by control loop).
        
        Args:
            dt: Time step in seconds
        """
        # Read hardware state
        cell_voltages = self.hardware.read_all_cell_voltages()
        pack_current = self.hardware.read_pack_current()
        temperatures = self.hardware.read_all_temperatures()
        
        # Update battery pack states
        for i, (voltage, temp) in enumerate(zip(cell_voltages, temperatures)):
            series_idx = i // self.pack_config.get("cells_in_parallel", 1)
            parallel_idx = i % self.pack_config.get("cells_in_parallel", 1)
            
            # Update SOC estimation
            soc = self.soc_estimator.update(pack_current, voltage, dt)
            
            # Update pack cell state
            self.battery_pack.update_cell_state(
                series_idx, parallel_idx,
                voltage, soc, temp + 273.15, pack_current
            )
        
        # Protection checks
        protection_result = self.protection_system.check_protections(
            cell_voltages=cell_voltages,
            pack_current=pack_current,
            temperatures=temperatures,
            pack=self.battery_pack
        )
        
        # Handle protection faults
        if protection_result.has_fault:
            self._handle_protection_fault(protection_result)
        else:
            # Normal operation
            if self.state == BMSState.FAULT or self.state == BMSState.EMERGENCY:
                # Fault cleared
                self._transition_state(BMSState.IDLE)
        
        # State machine logic
        self._update_state_machine(pack_current, dt)
        
        # Balancing control
        if self.balancing_enabled and self.state not in [BMSState.FAULT, BMSState.EMERGENCY]:
            self._update_balancing(dt)
        
        # Update control outputs
        self._update_control_outputs()
        
        # Update status
        self._update_status(protection_result)
        
        self.last_update_time = time.time()
    
    def _update_state_machine(self, pack_current: float, dt: float):
        """Update BMS state machine."""
        if self.state == BMSState.EMERGENCY:
            # Emergency state - no operations allowed
            return
        
        if self.state == BMSState.FAULT:
            # Fault state - wait for manual reset or fault clearance
            return
        
        # State transitions based on current
        if abs(pack_current) < 0.1:  # Less than 100mA
            if self.state != BMSState.IDLE and self.state != BMSState.BALANCING:
                self._transition_state(BMSState.IDLE)
        elif pack_current < 0:  # Charging (negative current)
            if self.state != BMSState.CHARGING:
                if self.charge_enabled:
                    self._transition_state(BMSState.CHARGING)
                else:
                    # Charging requested but not enabled
                    self._transition_state(BMSState.IDLE)
        elif pack_current > 0:  # Discharging (positive current)
            if self.state != BMSState.DISCHARGING:
                if self.discharge_enabled:
                    self._transition_state(BMSState.DISCHARGING)
                else:
                    # Discharging requested but not enabled
                    self._transition_state(BMSState.IDLE)
    
    def _handle_protection_fault(self, protection_result):
        """Handle protection fault detection."""
        if protection_result.level == ProtectionLevel.EMERGENCY:
            self._transition_state(BMSState.EMERGENCY)
            # Immediate shutdown
            self.hardware.enable_charge(False)
            self.hardware.enable_discharge(False)
            # Notify callbacks
            for callback in self.fault_callbacks:
                callback(protection_result.faults, ProtectionLevel.EMERGENCY)
        
        elif protection_result.level == ProtectionLevel.ALARM:
            self._transition_state(BMSState.FAULT)
            # Disable operations
            self.hardware.enable_charge(False)
            self.hardware.enable_discharge(False)
            # Notify callbacks
            for callback in self.fault_callbacks:
                callback(protection_result.faults, ProtectionLevel.ALARM)
        
        elif protection_result.level == ProtectionLevel.PRE_ALARM:
            # Reduce power but continue operation
            # Could implement power limiting here
            for callback in self.fault_callbacks:
                callback(protection_result.faults, ProtectionLevel.PRE_ALARM)
        
        elif protection_result.level == ProtectionLevel.WARNING:
            # Just log warning
            for callback in self.fault_callbacks:
                callback(protection_result.faults, ProtectionLevel.WARNING)
    
    def _update_balancing(self, dt: float):
        """Update cell balancing."""
        if self.balancer.is_balancing_needed(self.battery_pack):
            # Perform balancing
            balance_result = self.balancer.balance(self.battery_pack, dt)
            
            # Enable balancing hardware for cells that need it
            # This is simplified - actual implementation would track which cells need balancing
            if balance_result.get("active_cells", 0) > 0:
                # Enable balancing for high cells
                # Simplified: enable balancing for all cells above average
                imbalance = self.battery_pack.get_cell_imbalance()
                avg_soc = imbalance["avg_soc"]
                
                for s_idx in range(self.battery_pack.cells_in_series):
                    for p_idx in range(self.battery_pack.cells_in_parallel):
                        cell = self.battery_pack.cells[s_idx][p_idx]
                        cell_id = s_idx * self.battery_pack.cells_in_parallel + p_idx
                        
                        if cell.soc > avg_soc + self.balancer.balancing_threshold * 100:
                            self.hardware.enable_balance(cell_id, True)
                        else:
                            self.hardware.enable_balance(cell_id, False)
        else:
            # Disable all balancing
            for i in range(self.battery_pack.total_cells):
                self.hardware.enable_balance(i, False)
    
    def _update_control_outputs(self):
        """Update control outputs to hardware."""
        # Update charge/discharge enables based on state
        if self.state == BMSState.CHARGING:
            self.hardware.enable_charge(self.charge_enabled)
        else:
            self.hardware.enable_charge(False)
        
        if self.state == BMSState.DISCHARGING:
            self.hardware.enable_discharge(self.discharge_enabled)
        else:
            self.hardware.enable_discharge(False)
    
    def _update_status(self, protection_result):
        """Update current status."""
        pack_stats = self.battery_pack.get_pack_statistics()
        
        self.current_status = BMSStatus(
            state=self.state,
            pack_voltage=pack_stats["pack_voltage"],
            pack_current=pack_stats["pack_current"],
            pack_soc=pack_stats["pack_soc"],
            pack_soh=pack_stats["pack_soh"],
            pack_temperature=pack_stats.get("imbalance", {}).get("max_temperature", 298.15),
            active_faults=protection_result.faults,
            balancing_active=self.balancer.is_balancing_needed(self.battery_pack),
            charge_enabled=self.charge_enabled,
            discharge_enabled=self.discharge_enabled,
            timestamp=time.time()
        )
        
        # Store in history (keep last 1000 entries)
        self.status_history.append(self.current_status)
        if len(self.status_history) > 1000:
            self.status_history.pop(0)
    
    def _transition_state(self, new_state: BMSState):
        """Transition to a new state."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.state_history.append((time.time(), new_state))
            
            # Notify callbacks
            for callback in self.state_change_callbacks:
                callback(old_state, new_state)
    
    def enable_charging(self, enable: bool):
        """Enable or disable charging."""
        if self.state in [BMSState.FAULT, BMSState.EMERGENCY]:
            return False
        
        self.charge_enabled = enable
        return True
    
    def enable_discharging(self, enable: bool):
        """Enable or disable discharging."""
        if self.state in [BMSState.FAULT, BMSState.EMERGENCY]:
            return False
        
        self.discharge_enabled = enable
        return True
    
    def reset_fault(self):
        """Reset fault state (manual reset)."""
        if self.state == BMSState.FAULT:
            # Check if faults are cleared
            # TODO: Implement actual fault check
            self._transition_state(BMSState.IDLE)
            return True
        return False
    
    def get_status(self) -> BMSStatus:
        """Get current BMS status."""
        return self.current_status
    
    def get_statistics(self) -> Dict:
        """Get BMS statistics."""
        runtime = time.time() - self.start_time
        return {
            "runtime_seconds": runtime,
            "runtime_hours": runtime / 3600.0,
            "cycle_count": self.cycle_count,
            "total_energy_charged_wh": self.total_energy_charged,
            "total_energy_discharged_wh": self.total_energy_discharged,
            "current_state": self.state.value,
            "state_transitions": len(self.state_history)
        }
    
    def register_state_change_callback(self, callback: Callable):
        """Register callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def register_fault_callback(self, callback: Callable):
        """Register callback for fault events."""
        self.fault_callbacks.append(callback)
    
    def start_control_loop(self):
        """Start the control loop (for real-time operation)."""
        if self.control_loop_running:
            return
        
        self.control_loop_running = True
        # Control loop would run in a separate thread
        # This is a placeholder - actual implementation would use threading
    
    def stop_control_loop(self):
        """Stop the control loop."""
        self.control_loop_running = False

