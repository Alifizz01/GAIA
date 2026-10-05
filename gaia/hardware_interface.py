"""
Hardware Abstraction Layer (HAL) for GAIA BMS Framework
Provides unified interface for simulation and real hardware access.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import numpy as np


class HardwareInterface(ABC):
    """
    Abstract base class for hardware interfaces.
    Defines the contract that all hardware interfaces must implement.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize hardware connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close hardware connection and cleanup resources."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if hardware is connected."""
        pass
    
    @abstractmethod
    def read_cell_voltage(self, cell_id: int) -> float:
        """
        Read voltage from a specific cell.
        
        Args:
            cell_id: Cell identifier (0-indexed)
            
        Returns:
            Cell voltage in Volts
        """
        pass
    
    @abstractmethod
    def read_all_cell_voltages(self) -> List[float]:
        """
        Read voltages from all cells.
        
        Returns:
            List of cell voltages in Volts
        """
        pass
    
    @abstractmethod
    def read_pack_current(self) -> float:
        """
        Read pack current.
        
        Returns:
            Pack current in Amperes (positive for discharge, negative for charge)
        """
        pass
    
    @abstractmethod
    def read_temperature(self, sensor_id: int) -> float:
        """
        Read temperature from a sensor.
        
        Args:
            sensor_id: Temperature sensor identifier
            
        Returns:
            Temperature in Kelvin
        """
        pass
    
    @abstractmethod
    def read_all_temperatures(self) -> List[float]:
        """
        Read temperatures from all sensors.
        
        Returns:
            List of temperatures in Kelvin
        """
        pass
    
    @abstractmethod
    def enable_charge(self, enable: bool) -> bool:
        """
        Enable or disable charging.
        
        Args:
            enable: True to enable charging, False to disable
            
        Returns:
            True if command succeeded
        """
        pass
    
    @abstractmethod
    def enable_discharge(self, enable: bool) -> bool:
        """
        Enable or disable discharging.
        
        Args:
            enable: True to enable discharging, False to disable
            
        Returns:
            True if command succeeded
        """
        pass
    
    @abstractmethod
    def enable_balance(self, cell_id: int, enable: bool) -> bool:
        """
        Enable or disable balancing for a specific cell.
        
        Args:
            cell_id: Cell identifier
            enable: True to enable balancing, False to disable
            
        Returns:
            True if command succeeded
        """
        pass
    
    @abstractmethod
    def get_hardware_info(self) -> Dict:
        """
        Get hardware information and capabilities.
        
        Returns:
            Dictionary with hardware information
        """
        pass


class SimulationHardwareInterface(HardwareInterface):
    """
    Simulated battery pack behind the hardware interface.

    Every cell is an equivalent-circuit model with a lumped thermal mass:

        V    = OCV(SOC) - I*R0 - V_rc          OCV table from GAIA's PyBaMM model
        V_rc : dV_rc/dt = (I*R1 - V_rc) / (R1*C1)
        C_th * dT/dt = I^2*R0 + V_rc^2/R1 - hA*(T - T_ambient)

    Current only flows when the BMS has closed the matching contactor
    (discharge_enabled for I > 0, charge_enabled for I < 0), so protection
    actions have a physical effect. Balancing bleeds a fixed current through
    each enabled cell's resistor.

    pack_config keys: cells_in_series, cells_in_parallel, nominal_capacity
    (Ah per cell), chemistry, initial_soc [%], initial_temperature [K],
    ambient_temperature [K], cell_variation {"capacity", "resistance"
    (relative std), "soc" (% std)}, balance_current [A], sensor_noise (bool),
    seed. Sizes scale with capacity, so a 5 Ah and a 50 Ah cell behave alike
    at the same C-rate.
    """

    def __init__(self, pack_config: Dict, battery_model_config: Optional[Dict] = None):
        from .ocv import ocv_curve
        cfg = {**(battery_model_config or {}), **pack_config}
        self.pack_config = pack_config
        self.battery_model_config = battery_model_config or {}
        self.cells_in_series = cfg.get("cells_in_series", 1)
        self.cells_in_parallel = cfg.get("cells_in_parallel", 1)
        self.total_cells = self.cells_in_series * self.cells_in_parallel
        self.chemistry = cfg.get("chemistry", "NMC")
        self.ocv_curve = ocv_curve(self.chemistry)
        self.ambient_temperature = cfg.get("ambient_temperature", 298.15)
        self.balance_current = cfg.get("balance_current", 0.1)          # A per bleeding cell
        self.rng = np.random.default_rng(cfg.get("seed"))

        # Control states
        self.charge_enabled = False
        self.discharge_enabled = False
        self.balancing_enabled: Dict[int, bool] = {i: False for i in range(self.total_cells)}

        # Sensor noise (set sensor_noise=False for deterministic runs)
        noisy = cfg.get("sensor_noise", True)
        self.voltage_noise_std = 0.002 if noisy else 0.0      # V
        self.current_noise_std = 0.02 if noisy else 0.0       # A
        self.temperature_noise_std = 0.2 if noisy else 0.0    # K

        cap = cfg.get("nominal_capacity", 50.0)
        var = cfg.get("cell_variation", {})
        soc0 = cfg.get("initial_soc", 100.0)
        t0 = cfg.get("initial_temperature", self.ambient_temperature)
        self.cell_states: List[Dict] = []
        for _ in range(self.total_cells):
            c = cap * (1 + self.rng.normal(0, var.get("capacity", 0.0)))
            r_scale = 1 + self.rng.normal(0, var.get("resistance", 0.0))
            state = {
                "capacity": c,                                  # Ah
                "internal_resistance": 0.06 / c * r_scale,      # R0 [ohm], ~1.2 mOhm for 50 Ah
                "r1": 0.03 / c * r_scale,                       # polarisation resistance [ohm]
                "tau": 30.0,                                    # R1*C1 [s]
                "thermal_mass": 18.0 * c,                       # J/K
                "h_a": 0.006 * c,                               # W/K to ambient
                "soc": float(np.clip(soc0 + self.rng.normal(0, var.get("soc", 0.0)), 0, 100)),
                "v_rc": 0.0,
                "temperature": t0,
                "current": 0.0,
                "soh": 100.0,
            }
            state["voltage"] = float(self.ocv_curve.ocv(state["soc"]))
            self.cell_states.append(state)

        self.current_time = 0.0
        self.time_step = 0.1
        self.connected = False
        self.pack_current = 0.0
        self.requested_current = 0.0

    def initialize(self) -> bool:
        self.connected = True
        self.current_time = 0.0
        return True

    def close(self):
        self.connected = False
        self.charge_enabled = False
        self.discharge_enabled = False

    def is_connected(self) -> bool:
        return self.connected

    def read_cell_voltage(self, cell_id: int) -> float:
        if not (0 <= cell_id < self.total_cells):
            raise ValueError(f"Invalid cell_id: {cell_id}")
        return self.cell_states[cell_id]["voltage"] + self.rng.normal(0, self.voltage_noise_std)

    def read_all_cell_voltages(self) -> List[float]:
        return [self.read_cell_voltage(i) for i in range(self.total_cells)]

    def read_pack_current(self) -> float:
        return self.pack_current + self.rng.normal(0, self.current_noise_std)

    def read_temperature(self, sensor_id: int) -> float:
        """Kelvin. One sensor per cell; an unknown id returns the pack average."""
        if not (0 <= sensor_id < self.total_cells):
            return float(np.mean([s["temperature"] for s in self.cell_states]))
        return self.cell_states[sensor_id]["temperature"] + self.rng.normal(0, self.temperature_noise_std)

    def read_all_temperatures(self) -> List[float]:
        return [self.read_temperature(i) for i in range(self.total_cells)]

    def enable_charge(self, enable: bool) -> bool:
        self.charge_enabled = enable
        return True

    def enable_discharge(self, enable: bool) -> bool:
        self.discharge_enabled = enable
        return True

    def enable_balance(self, cell_id: int, enable: bool) -> bool:
        if not (0 <= cell_id < self.total_cells):
            return False
        self.balancing_enabled[cell_id] = enable
        return True

    def update_simulation(self, dt: float, pack_current: Optional[float] = None):
        """Advance the pack by dt seconds with the requested pack current
        (A, positive = discharge). The contactors decide what actually flows."""
        if not self.connected:
            return
        self.current_time += dt
        if pack_current is not None:
            self.requested_current = pack_current
        i = self.requested_current
        if (i > 0 and not self.discharge_enabled) or (i < 0 and not self.charge_enabled):
            i = 0.0
        self.pack_current = i

        # ponytail: parallel cells share current equally (no circulating
        # current between mismatched cells); model branches if that matters.
        branch = i / self.cells_in_parallel
        for cid, s in enumerate(self.cell_states):
            # leak_current models an internal short: charge that drains inside the cell
            ic = branch + (self.balance_current if self.balancing_enabled.get(cid) else 0.0) + s.get("leak_current", 0.0)
            s["current"] = ic
            s["soc"] = float(np.clip(s["soc"] - ic * dt / 3600.0 / s["capacity"] * 100.0, -5.0, 105.0))
            r1 = s["r1"]
            decay = np.exp(-dt / s["tau"])
            s["v_rc"] = ic * r1 + (s["v_rc"] - ic * r1) * decay
            s["voltage"] = float(self._ocv(s["soc"]) - ic * s["internal_resistance"] - s["v_rc"])
            heat = ic * ic * s["internal_resistance"] + s["v_rc"] ** 2 / r1
            s["temperature"] += (heat - s["h_a"] * (s["temperature"] - self.ambient_temperature)) / s["thermal_mass"] * dt

    def _ocv(self, soc: float) -> float:
        """OCV, extended past the table: beyond empty the voltage collapses
        (1 V per % SOC), beyond full it climbs (0.05 V per %), so an
        over-discharge or over-charge reaches the protection thresholds the
        way a real cell does instead of sitting at the table's end value."""
        if soc < 0.0:
            return self.ocv_curve.v_min + 1.0 * soc
        if soc > 100.0:
            return self.ocv_curve.v_max + 0.05 * (soc - 100.0)
        return float(self.ocv_curve.ocv(soc))

    def set_cell_state(self, cell_id: int, state: Dict):
        """Override cell state directly (fault injection: temperature, soc,
        internal_resistance, capacity, ...)."""
        if 0 <= cell_id < self.total_cells:
            self.cell_states[cell_id].update(state)

    def get_cell_state(self, cell_id: int) -> Dict:
        if 0 <= cell_id < self.total_cells:
            return self.cell_states[cell_id].copy()
        return {}

    def get_all_cell_states(self) -> List[Dict]:
        return [state.copy() for state in self.cell_states]

    def get_hardware_info(self) -> Dict:
        return {
            "type": "simulation",
            "model": "equivalent circuit (OCV + R0 + RC) with lumped thermal mass",
            "cells_in_series": self.cells_in_series,
            "cells_in_parallel": self.cells_in_parallel,
            "total_cells": self.total_cells,
            "chemistry": self.chemistry,
            "charge_enabled": self.charge_enabled,
            "discharge_enabled": self.discharge_enabled,
            "connected": self.connected,
        }


class RealHardwareInterface(HardwareInterface):
    """
    Hardware interface implementation for real hardware.
    Placeholder for future implementation - will connect to actual BMS hardware.
    """
    
    def __init__(self, connection_params: Dict):
        """
        Initialize real hardware interface.
        
        Args:
            connection_params: Connection parameters (protocol, address, port, etc.)
        """
        self.connection_params = connection_params
        self.connected = False
        self.protocol = connection_params.get("protocol", "CAN")  # CAN, I2C, SPI, Modbus, etc.
        
    def initialize(self) -> bool:
        """Initialize real hardware connection."""
        # TODO: Implement actual hardware initialization
        # Example: Initialize CAN bus, I2C, SPI, etc.
        print(f"Initializing {self.protocol} hardware interface...")
        self.connected = True
        return True
    
    def close(self):
        """Close hardware connection."""
        # TODO: Implement actual hardware cleanup
        self.connected = False
    
    def is_connected(self) -> bool:
        """Check if hardware is connected."""
        return self.connected
    
    def read_cell_voltage(self, cell_id: int) -> float:
        """Read voltage from real hardware."""
        # TODO: Implement actual hardware reading
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def read_all_cell_voltages(self) -> List[float]:
        """Read all cell voltages from hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def read_pack_current(self) -> float:
        """Read pack current from hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def read_temperature(self, sensor_id: int) -> float:
        """Read temperature from hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def read_all_temperatures(self) -> List[float]:
        """Read all temperatures from hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def enable_charge(self, enable: bool) -> bool:
        """Enable/disable charging on hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def enable_discharge(self, enable: bool) -> bool:
        """Enable/disable discharging on hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def enable_balance(self, cell_id: int, enable: bool) -> bool:
        """Enable/disable balancing on hardware."""
        # TODO: Implement
        raise NotImplementedError("Real hardware interface not yet implemented")
    
    def get_hardware_info(self) -> Dict:
        """Get real hardware information."""
        return {
            "type": "real_hardware",
            "protocol": self.protocol,
            "connected": self.connected,
            "connection_params": self.connection_params
        }

