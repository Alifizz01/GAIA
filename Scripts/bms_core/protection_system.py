"""
Protection System for GAIA BMS Framework
Implements safety protection functions (overvoltage, overcurrent, overtemperature, etc.)
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from .battery_pack import BatteryPack


class ProtectionLevel(Enum):
    """Protection alarm levels."""
    OK = "ok"
    WARNING = "warning"
    PRE_ALARM = "pre_alarm"
    ALARM = "alarm"
    EMERGENCY = "emergency"


class ProtectionFaultType(Enum):
    """Types of faults detected by protection system."""
    OVERVOLTAGE = "overvoltage"
    UNDERVOLTAGE = "undervoltage"
    OVERCURRENT_CHARGE = "overcurrent_charge"
    OVERCURRENT_DISCHARGE = "overcurrent_discharge"
    OVERTEMPERATURE = "overtemperature"
    UNDERTEMPERATURE = "undertemperature"
    CELL_IMBALANCE = "cell_imbalance"
    SHORT_CIRCUIT = "short_circuit"
    OPEN_CIRCUIT = "open_circuit"
    INTERNAL_FAULT = "internal_fault"


@dataclass
class ProtectionResult:
    """Result of protection system check."""
    has_fault: bool
    level: ProtectionLevel
    faults: List[ProtectionFaultType]
    details: Dict


class ProtectionSystem:
    """
    Protection system implementing safety functions for BMS.
    
    Monitors:
    - Cell voltages (overvoltage, undervoltage)
    - Pack current (overcurrent, short circuit)
    - Temperatures (overtemperature, undertemperature)
    - Cell imbalance
    """
    
    def __init__(self, protection_config: Dict):
        """
        Initialize protection system.
        
        Args:
            protection_config: Protection configuration with thresholds
        """
        self.config = protection_config
        
        # Voltage protection thresholds
        self.overvoltage_threshold = protection_config.get("overvoltage_threshold", 4.25)  # V
        self.undervoltage_threshold = protection_config.get("undervoltage_threshold", 2.5)  # V
        self.overvoltage_warning = protection_config.get("overvoltage_warning", 4.15)  # V
        self.undervoltage_warning = protection_config.get("undervoltage_warning", 3.0)  # V
        
        # Current protection thresholds
        self.overcurrent_charge_threshold = protection_config.get("overcurrent_charge_threshold", -50.0)  # A (negative)
        self.overcurrent_discharge_threshold = protection_config.get("overcurrent_discharge_threshold", 100.0)  # A
        self.short_circuit_threshold = protection_config.get("short_circuit_threshold", 500.0)  # A
        self.short_circuit_time = protection_config.get("short_circuit_time", 0.001)  # s
        
        # Temperature protection thresholds
        self.overtemperature_threshold = protection_config.get("overtemperature_threshold", 60.0) + 273.15  # K
        self.undertemperature_threshold = protection_config.get("undertemperature_threshold", -20.0) + 273.15  # K
        self.overtemperature_warning = protection_config.get("overtemperature_warning", 45.0) + 273.15  # K
        self.undertemperature_warning = protection_config.get("undertemperature_warning", 0.0) + 273.15  # K
        
        # Imbalance protection
        self.imbalance_threshold = protection_config.get("imbalance_threshold", 0.2)  # V
        
        # Fault history
        self.fault_history: List[tuple] = []  # (timestamp, fault_type, level)
        self.active_faults: List[ProtectionFaultType] = []
        
        # Short circuit detection
        self.last_current = 0.0
        self.current_rise_time = 0.0
        self.short_circuit_detected = False
    
    def check_protections(self,
                         cell_voltages: List[float],
                         pack_current: float,
                         temperatures: List[float],
                         pack: Optional[BatteryPack] = None) -> ProtectionResult:
        """
        Check all protection functions.
        
        Args:
            cell_voltages: List of cell voltages in Volts
            pack_current: Pack current in Amperes
            temperatures: List of temperatures in Kelvin
            pack: Optional BatteryPack for imbalance checking
            
        Returns:
            ProtectionResult with fault information
        """
        faults: List[ProtectionFaultType] = []
        max_level = ProtectionLevel.OK
        details: Dict = {}
        
        # Check voltage protections
        voltage_result = self._check_voltage_protections(cell_voltages)
        if voltage_result["has_fault"]:
            faults.extend(voltage_result["faults"])
            if self._get_level_priority(voltage_result["level"]) > self._get_level_priority(max_level):
                max_level = voltage_result["level"]
            details["voltage"] = voltage_result["details"]
        
        # Check current protections
        current_result = self._check_current_protections(pack_current)
        if current_result["has_fault"]:
            faults.extend(current_result["faults"])
            if self._get_level_priority(current_result["level"]) > self._get_level_priority(max_level):
                max_level = current_result["level"]
            details["current"] = current_result["details"]
        
        # Check temperature protections
        temp_result = self._check_temperature_protections(temperatures)
        if temp_result["has_fault"]:
            faults.extend(temp_result["faults"])
            if self._get_level_priority(temp_result["level"]) > self._get_level_priority(max_level):
                max_level = temp_result["level"]
            details["temperature"] = temp_result["details"]
        
        # Check imbalance
        if pack is not None:
            imbalance_result = self._check_imbalance(pack)
            if imbalance_result["has_fault"]:
                faults.extend(imbalance_result["faults"])
                if self._get_level_priority(imbalance_result["level"]) > self._get_level_priority(max_level):
                    max_level = imbalance_result["level"]
                details["imbalance"] = imbalance_result["details"]
        
        # Update active faults
        self.active_faults = faults.copy()
        
        return ProtectionResult(
            has_fault=len(faults) > 0,
            level=max_level,
            faults=faults,
            details=details
        )
    
    def _check_voltage_protections(self, cell_voltages: List[float]) -> Dict:
        """Check voltage protection functions."""
        faults: List[ProtectionFaultType] = []
        max_level = ProtectionLevel.OK
        details = {
            "max_voltage": max(cell_voltages) if cell_voltages else 0.0,
            "min_voltage": min(cell_voltages) if cell_voltages else 0.0,
            "fault_cells": []
        }
        
        for i, voltage in enumerate(cell_voltages):
            # Overvoltage protection
            if voltage > self.overvoltage_threshold:
                faults.append(ProtectionFaultType.OVERVOLTAGE)
                details["fault_cells"].append({"cell": i, "fault": "overvoltage", "voltage": voltage})
                max_level = ProtectionLevel.EMERGENCY
            
            elif voltage > self.overvoltage_warning:
                if max_level == ProtectionLevel.OK:
                    max_level = ProtectionLevel.WARNING
                details["fault_cells"].append({"cell": i, "fault": "overvoltage_warning", "voltage": voltage})
            
            # Undervoltage protection
            elif voltage < self.undervoltage_threshold:
                faults.append(ProtectionFaultType.UNDERVOLTAGE)
                details["fault_cells"].append({"cell": i, "fault": "undervoltage", "voltage": voltage})
                if max_level != ProtectionLevel.EMERGENCY:
                    max_level = ProtectionLevel.ALARM
            
            elif voltage < self.undervoltage_warning:
                if max_level == ProtectionLevel.OK:
                    max_level = ProtectionLevel.WARNING
                details["fault_cells"].append({"cell": i, "fault": "undervoltage_warning", "voltage": voltage})
        
        return {
            "has_fault": len(faults) > 0,
            "level": max_level,
            "faults": faults,
            "details": details
        }
    
    def _check_current_protections(self, pack_current: float) -> Dict:
        """Check current protection functions."""
        faults: List[ProtectionFaultType] = []
        level = ProtectionLevel.OK
        details = {"current": pack_current}
        
        # Short circuit detection (rapid current rise)
        current_rise_rate = abs(pack_current - self.last_current) / 0.1  # A/s (assuming 100ms update)
        
        if abs(pack_current) > self.short_circuit_threshold:
            faults.append(ProtectionFaultType.SHORT_CIRCUIT)
            level = ProtectionLevel.EMERGENCY
            details["short_circuit"] = True
            self.short_circuit_detected = True
        
        elif current_rise_rate > 1000.0:  # Very rapid rise
            faults.append(ProtectionFaultType.SHORT_CIRCUIT)
            level = ProtectionLevel.EMERGENCY
            details["short_circuit"] = True
            details["rise_rate"] = current_rise_rate
            self.short_circuit_detected = True
        
        # Overcurrent protection
        elif pack_current < self.overcurrent_charge_threshold:  # Charging overcurrent (negative)
            faults.append(ProtectionFaultType.OVERCURRENT_CHARGE)
            level = ProtectionLevel.ALARM
            details["overcurrent_type"] = "charge"
        
        elif pack_current > self.overcurrent_discharge_threshold:  # Discharging overcurrent (positive)
            faults.append(ProtectionFaultType.OVERCURRENT_DISCHARGE)
            level = ProtectionLevel.ALARM
            details["overcurrent_type"] = "discharge"
        
        # Update last current
        self.last_current = pack_current
        
        return {
            "has_fault": len(faults) > 0,
            "level": level,
            "faults": faults,
            "details": details
        }
    
    def _check_temperature_protections(self, temperatures: List[float]) -> Dict:
        """Check temperature protection functions."""
        faults: List[ProtectionFaultType] = []
        max_level = ProtectionLevel.OK
        details = {
            "max_temperature": max(temperatures) if temperatures else 298.15,
            "min_temperature": min(temperatures) if temperatures else 298.15,
            "fault_sensors": []
        }
        
        for i, temp in enumerate(temperatures):
            # Overtemperature protection
            if temp > self.overtemperature_threshold:
                faults.append(ProtectionFaultType.OVERTEMPERATURE)
                details["fault_sensors"].append({"sensor": i, "fault": "overtemperature", "temperature": temp})
                max_level = ProtectionLevel.EMERGENCY
            
            elif temp > self.overtemperature_warning:
                if max_level == ProtectionLevel.OK or max_level == ProtectionLevel.WARNING:
                    max_level = ProtectionLevel.PRE_ALARM
                details["fault_sensors"].append({"sensor": i, "fault": "overtemperature_warning", "temperature": temp})
            
            # Undertemperature protection
            elif temp < self.undertemperature_threshold:
                faults.append(ProtectionFaultType.UNDERTEMPERATURE)
                details["fault_sensors"].append({"sensor": i, "fault": "undertemperature", "temperature": temp})
                if max_level != ProtectionLevel.EMERGENCY:
                    max_level = ProtectionLevel.ALARM
            
            elif temp < self.undertemperature_warning:
                if max_level == ProtectionLevel.OK:
                    max_level = ProtectionLevel.WARNING
                details["fault_sensors"].append({"sensor": i, "fault": "undertemperature_warning", "temperature": temp})
        
        return {
            "has_fault": len(faults) > 0,
            "level": max_level,
            "faults": faults,
            "details": details
        }
    
    def _check_imbalance(self, pack: BatteryPack) -> Dict:
        """Check cell imbalance protection."""
        imbalance = pack.get_cell_imbalance()
        voltage_diff = imbalance["max_voltage"] - imbalance["min_voltage"]
        soc_diff = imbalance["max_soc"] - imbalance["min_soc"]
        
        faults: List[ProtectionFaultType] = []
        level = ProtectionLevel.OK
        details = {
            "voltage_diff": voltage_diff,
            "soc_diff": soc_diff,
            "imbalance": imbalance
        }
        
        if voltage_diff > self.imbalance_threshold:
            faults.append(ProtectionFaultType.CELL_IMBALANCE)
            level = ProtectionLevel.PRE_ALARM
            details["fault"] = "voltage_imbalance"
        elif soc_diff > 10.0:  # 10% SOC difference
            if level == ProtectionLevel.OK:
                level = ProtectionLevel.WARNING
            details["fault"] = "soc_imbalance"
        
        return {
            "has_fault": len(faults) > 0,
            "level": level,
            "faults": faults,
            "details": details
        }
    
    def _get_level_priority(self, level: ProtectionLevel) -> int:
        """Get priority level for comparison (higher = more severe)."""
        priorities = {
            ProtectionLevel.OK: 0,
            ProtectionLevel.WARNING: 1,
            ProtectionLevel.PRE_ALARM: 2,
            ProtectionLevel.ALARM: 3,
            ProtectionLevel.EMERGENCY: 4
        }
        return priorities.get(level, 0)
    
    def get_active_faults(self) -> List[ProtectionFaultType]:
        """Get list of currently active faults."""
        return self.active_faults.copy()
    
    def clear_faults(self):
        """Clear all active faults."""
        self.active_faults.clear()
        self.short_circuit_detected = False

