"""
Charging and Discharging Simulation Module for GAIA BMS Framework
Implements various charging/discharging protocols including CC/CV, profiles, and load simulation.
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass


class ChargingMode(Enum):
    """Charging modes."""
    CONSTANT_CURRENT = "constant_current"
    CONSTANT_VOLTAGE = "constant_voltage"
    CONSTANT_CURRENT_CONSTANT_VOLTAGE = "cc_cv"  # CC-CV charging
    PULSE_CHARGING = "pulse_charging"
    FAST_CHARGING = "fast_charging"
    TRICKLE_CHARGING = "trickle_charging"


class DischargingMode(Enum):
    """Discharging modes."""
    CONSTANT_CURRENT = "constant_current"
    CONSTANT_POWER = "constant_power"
    CONSTANT_RESISTANCE = "constant_resistance"
    PULSE_DISCHARGING = "pulse_discharging"
    LOAD_PROFILE = "load_profile"


@dataclass
class ChargingProfile:
    """Defines a charging profile."""
    mode: ChargingMode
    cc_current: float = 1.0  # Constant current in C-rate or Amperes
    cv_voltage: float = 4.2  # Constant voltage in Volts
    termination_current: float = 0.05  # Termination current in C-rate or Amperes
    max_time: Optional[float] = None  # Maximum charging time in seconds
    temperature_limit: float = 45.0  # Temperature limit in °C


@dataclass
class DischargingProfile:
    """Defines a discharging profile."""
    mode: DischargingMode
    current: Optional[float] = None  # Current in C-rate or Amperes
    power: Optional[float] = None  # Power in Watts
    resistance: Optional[float] = None  # Resistance in Ohms
    min_voltage: float = 2.5  # Minimum voltage cutoff in Volts
    max_time: Optional[float] = None  # Maximum discharging time in seconds


class ChargingController:
    """
    Controller for battery charging operations.
    Implements various charging protocols including CC-CV.
    """
    
    def __init__(self, profile: ChargingProfile):
        """
        Initialize charging controller.
        
        Args:
            profile: Charging profile to follow
        """
        self.profile = profile
        self.charging_phase = "cc"  # "cc" or "cv"
        self.is_complete = False
        
    def calculate_current(self, voltage: float, soc: float, temperature: float,
                         nominal_capacity: float = 50.0) -> float:
        """
        Calculate charging current based on profile and battery state.
        
        Args:
            voltage: Current cell voltage (V)
            soc: Current SOC (%)
            temperature: Current temperature (°C or K)
            nominal_capacity: Nominal battery capacity (Ah)
            
        Returns:
            Charging current (A, negative for charging)
        """
        if self.is_complete:
            return 0.0
        
        # Temperature check
        temp_celsius = temperature - 273.15 if temperature > 100 else temperature
        if temp_celsius > self.profile.temperature_limit:
            return 0.0  # Stop charging if too hot
        
        # Convert C-rate to current if needed
        if self.profile.cc_current < 10:  # Assume C-rate if < 10
            cc_current = self.profile.cc_current * nominal_capacity
        else:
            cc_current = self.profile.cc_current
        
        termination_current = (
            self.profile.termination_current * nominal_capacity 
            if self.profile.termination_current < 1.0 
            else self.profile.termination_current
        )
        
        if self.profile.mode == ChargingMode.CONSTANT_CURRENT:
            return -cc_current  # Negative for charging
        
        elif self.profile.mode == ChargingMode.CONSTANT_VOLTAGE:
            # Constant voltage charging (voltage-limited)
            if voltage < self.profile.cv_voltage:
                return -cc_current
            else:
                return 0.0
        
        elif self.profile.mode == ChargingMode.CONSTANT_CURRENT_CONSTANT_VOLTAGE:
            # CC-CV charging protocol
            if self.charging_phase == "cc":
                if voltage < self.profile.cv_voltage:
                    return -cc_current
                else:
                    self.charging_phase = "cv"
                    return -cc_current  # Transition to CV
            else:  # CV phase
                if voltage >= self.profile.cv_voltage:
                    # Voltage reached, maintain constant voltage
                    # Current will naturally decrease
                    current = -min(cc_current, (self.profile.cv_voltage - voltage) * 100)
                    # Check termination condition
                    if abs(current) < termination_current:
                        self.is_complete = True
                        return 0.0
                    return current
                else:
                    # Voltage dropped, switch back to CC
                    self.charging_phase = "cc"
                    return -cc_current
        
        elif self.profile.mode == ChargingMode.FAST_CHARGING:
            # Fast charging with higher current
            fast_current = cc_current * 2.0  # 2C rate
            if voltage < self.profile.cv_voltage:
                return -fast_current
            else:
                return -cc_current  # Reduce to normal current
        
        elif self.profile.mode == ChargingMode.TRICKLE_CHARGING:
            # Trickle charging with low current
            trickle_current = cc_current * 0.1  # 0.1C rate
            if soc < 100.0:
                return -trickle_current
            else:
                return 0.0
        
        return 0.0
    
    def is_charging_complete(self) -> bool:
        """Check if charging is complete."""
        return self.is_complete


class DischargingController:
    """
    Controller for battery discharging operations.
    Implements various discharging modes and load profiles.
    """
    
    def __init__(self, profile: DischargingProfile, load_profile: Optional[Callable] = None):
        """
        Initialize discharging controller.
        
        Args:
            profile: Discharging profile to follow
            load_profile: Optional function f(t) that returns load current at time t
        """
        self.profile = profile
        self.load_profile = load_profile
        self.is_complete = False
        
    def calculate_current(self, voltage: float, soc: float, time: float = 0.0,
                         nominal_capacity: float = 50.0) -> float:
        """
        Calculate discharging current based on profile and battery state.
        
        Args:
            voltage: Current cell voltage (V)
            soc: Current SOC (%)
            time: Current time (s)
            nominal_capacity: Nominal battery capacity (Ah)
            
        Returns:
            Discharging current (A, positive for discharging)
        """
        if self.is_complete:
            return 0.0
        
        # Voltage cutoff check
        if voltage < self.profile.min_voltage:
            self.is_complete = True
            return 0.0
        
        # SOC check
        if soc <= 0.0:
            self.is_complete = True
            return 0.0
        
        if self.profile.mode == DischargingMode.CONSTANT_CURRENT:
            if self.profile.current is None:
                raise ValueError("Current must be specified for constant current mode")
            current = self.profile.current
            if current < 10:  # Assume C-rate if < 10
                current = current * nominal_capacity
            return current
        
        elif self.profile.mode == DischargingMode.CONSTANT_POWER:
            if self.profile.power is None:
                raise ValueError("Power must be specified for constant power mode")
            # P = V * I, so I = P / V
            if voltage > 0:
                return self.profile.power / voltage
            else:
                return 0.0
        
        elif self.profile.mode == DischargingMode.CONSTANT_RESISTANCE:
            if self.profile.resistance is None:
                raise ValueError("Resistance must be specified for constant resistance mode")
            # I = V / R
            if self.profile.resistance > 0:
                return voltage / self.profile.resistance
            else:
                return 0.0
        
        elif self.profile.mode == DischargingMode.LOAD_PROFILE:
            if self.load_profile is not None:
                return self.load_profile(time)
            else:
                # Default: 1C discharge
                return nominal_capacity
        
        elif self.profile.mode == DischargingMode.PULSE_DISCHARGING:
            # Pulse discharging pattern
            pulse_freq = 1.0  # Hz
            duty_cycle = 0.5
            period = 1.0 / pulse_freq
            phase = (time % period) / period
            
            base_current = self.profile.current or nominal_capacity
            if base_current < 10:
                base_current = base_current * nominal_capacity
            
            if phase < duty_cycle:
                return base_current
            else:
                return 0.0
        
        return 0.0
    
    def is_discharging_complete(self) -> bool:
        """Check if discharging is complete."""
        return self.is_complete


class ChargeDischargeSimulator:
    """
    High-level simulator for charging and discharging operations.
    """
    
    def __init__(self, charging_profile: Optional[ChargingProfile] = None,
                 discharging_profile: Optional[DischargingProfile] = None):
        """
        Initialize charge/discharge simulator.
        
        Args:
            charging_profile: Charging profile (optional)
            discharging_profile: Discharging profile (optional)
        """
        self.charging_controller = ChargingController(charging_profile) if charging_profile else None
        self.discharging_controller = DischargingController(discharging_profile) if discharging_profile else None
        
    def simulate_charging_step(self, voltage: float, soc: float, temperature: float,
                              dt: float, nominal_capacity: float = 50.0) -> Dict:
        """
        Simulate one step of charging.
        
        Returns:
            Dictionary with current, energy added, etc.
        """
        if not self.charging_controller:
            raise ValueError("Charging profile not set")
        
        current = self.charging_controller.calculate_current(
            voltage, soc, temperature, nominal_capacity
        )
        
        # Calculate energy added
        energy_added = abs(current) * voltage * dt / 3600.0  # Wh
        
        return {
            "current": current,
            "energy_added": energy_added,
            "is_complete": self.charging_controller.is_charging_complete(),
            "phase": self.charging_controller.charging_phase
        }
    
    def simulate_discharging_step(self, voltage: float, soc: float, time: float,
                                 dt: float, nominal_capacity: float = 50.0) -> Dict:
        """
        Simulate one step of discharging.
        
        Returns:
            Dictionary with current, energy removed, etc.
        """
        if not self.discharging_controller:
            raise ValueError("Discharging profile not set")
        
        current = self.discharging_controller.calculate_current(
            voltage, soc, time, nominal_capacity
        )
        
        # Calculate energy removed
        energy_removed = current * voltage * dt / 3600.0  # Wh
        
        return {
            "current": current,
            "energy_removed": energy_removed,
            "is_complete": self.discharging_controller.is_discharging_complete()
        }
    
    def create_standard_charging_profile(self, c_rate: float = 1.0) -> ChargingProfile:
        """Create a standard CC-CV charging profile."""
        return ChargingProfile(
            mode=ChargingMode.CONSTANT_CURRENT_CONSTANT_VOLTAGE,
            cc_current=c_rate,
            cv_voltage=4.2,
            termination_current=0.05
        )
    
    def create_fast_charging_profile(self, c_rate: float = 2.0) -> ChargingProfile:
        """Create a fast charging profile."""
        return ChargingProfile(
            mode=ChargingMode.FAST_CHARGING,
            cc_current=c_rate,
            cv_voltage=4.2,
            termination_current=0.1,
            temperature_limit=45.0
        )
    
    def create_standard_discharging_profile(self, c_rate: float = 1.0) -> DischargingProfile:
        """Create a standard constant current discharging profile."""
        return DischargingProfile(
            mode=DischargingMode.CONSTANT_CURRENT,
            current=c_rate,
            min_voltage=2.5
        )

