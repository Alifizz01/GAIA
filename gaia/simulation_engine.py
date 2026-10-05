"""
Real-time Simulation Engine for GAIA BMS Framework
Orchestrates the complete simulation with BMS controller, hardware interface, and data acquisition.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
import numpy as np

from .hardware_interface import HardwareInterface, SimulationHardwareInterface
from .bms_controller import BMSController
from .data_logger import DataLogger
from .charging_discharging_simulation import ChargeDischargeSimulator, ChargingProfile, DischargingProfile


log = logging.getLogger("gaia")


class SimulationEngine:
    """
    Real-time simulation engine that runs BMS simulation with all components integrated.

    The engine:
    1. Initializes hardware interface and BMS controller
    2. Runs control loop at specified frequency
    3. Updates battery simulation models
    4. Executes BMS control logic
    5. Acquires and logs data
    6. Provides real-time status updates
    """

    def __init__(self,
                 hardware_interface: HardwareInterface,
                 pack_config: Dict,
                 bms_config: Optional[Dict] = None,
                 simulation_config: Optional[Dict] = None):
        """
        Initialize simulation engine.

        Args:
            hardware_interface: Hardware interface (simulation or real)
            pack_config: Pack configuration
            bms_config: BMS controller configuration
            simulation_config: Simulation configuration
        """
        self.hardware = hardware_interface
        self.pack_config = pack_config
        self.bms_config = bms_config or {}
        self.simulation_config = simulation_config or self._get_default_simulation_config()

        # Initialize BMS controller
        self.bms_controller = BMSController(
            hardware_interface=hardware_interface,
            pack_config=pack_config,
            bms_config=bms_config
        )

        # Data logging
        log_config = self.simulation_config.get("logging", {})
        if log_config.get("enabled", True):
            self.data_logger = DataLogger(
                log_directory=log_config.get("log_directory", "logs"),
                log_format=log_config.get("log_format", "csv")
            )
        else:
            self.data_logger = None

        # Charge/discharge simulator
        self.charge_discharge_simulator: Optional[ChargeDischargeSimulator] = None

        # Control loop
        self.control_loop_thread: Optional[threading.Thread] = None
        self.control_loop_running = False
        self.control_loop_frequency = self.simulation_config.get("control_loop_frequency", 10.0)  # Hz
        self.time_step = 1.0 / self.control_loop_frequency  # seconds

        # Simulation state
        self.simulation_time = 0.0
        self.simulation_running = False
        self.simulation_paused = False
        self.start_time: Optional[float] = None

        # Pack current control (for charge/discharge simulation)
        self.target_pack_current = 0.0
        self.charging_profile: Optional[ChargingProfile] = None
        self.discharging_profile: Optional[DischargingProfile] = None

        # Callbacks
        self._last_fault_key = None
        self.status_callbacks: List[Callable] = []
        self.fault_callbacks: List[Callable] = []

        # Statistics
        self.last_status_update = 0.0
        self.status_update_interval = 0.1  # 10 Hz status updates

    def _get_default_simulation_config(self) -> Dict:
        """Get default simulation configuration."""
        return {
            "control_loop_frequency": 10.0,  # Hz
            "simulation_duration": 3600.0,  # seconds
            "logging": {
                "enabled": True,
                "log_directory": "logs",
                "log_format": "csv",
                "log_interval": 1.0  # seconds
            }
        }

    def initialize(self) -> bool:
        """Initialize simulation engine."""
        if not self.bms_controller.initialize():
            return False

        # Register callbacks
        self.bms_controller.register_state_change_callback(self._on_state_change)
        self.bms_controller.register_fault_callback(self._on_fault)

        return True

    def close(self):
        """Close simulation engine and cleanup."""
        self.stop_simulation()
        self.bms_controller.close()
        if self.data_logger:
            self.data_logger.close()

    def start_simulation(self):
        """Start the simulation."""
        if self.simulation_running:
            return

        self.simulation_running = True
        self.simulation_paused = False
        self.simulation_time = 0.0
        self.start_time = time.time()

        # Start control loop thread
        self.control_loop_running = True
        self.control_loop_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_loop_thread.start()

    def stop_simulation(self):
        """Stop the simulation."""
        self.control_loop_running = False
        self.simulation_running = False

        if self.control_loop_thread:
            self.control_loop_thread.join(timeout=2.0)
            self.control_loop_thread = None

    def pause_simulation(self):
        """Pause the simulation."""
        self.simulation_paused = True

    def resume_simulation(self):
        """Resume the simulation."""
        self.simulation_paused = False

    def set_charging_profile(self, profile: ChargingProfile):
        """Set charging profile for simulation."""
        self.charging_profile = profile
        from .charging_discharging_simulation import ChargeDischargeSimulator
        self.charge_discharge_simulator = ChargeDischargeSimulator(charging_profile=profile)

    def set_discharging_profile(self, profile: DischargingProfile):
        """Set discharging profile for simulation."""
        self.discharging_profile = profile
        from .charging_discharging_simulation import ChargeDischargeSimulator
        self.charge_discharge_simulator = ChargeDischargeSimulator(discharging_profile=profile)

    def set_pack_current(self, current: float):
        """
        Set target pack current for simulation.

        Args:
            current: Target current in Amperes (positive = discharge, negative = charge)
        """
        self.target_pack_current = current

        # Update BMS controller enables
        if current < 0:  # Charging
            self.bms_controller.enable_charging(True)
            self.bms_controller.enable_discharging(False)
        elif current > 0:  # Discharging
            self.bms_controller.enable_charging(False)
            self.bms_controller.enable_discharging(True)
        else:  # No current
            self.bms_controller.enable_charging(False)
            self.bms_controller.enable_discharging(False)

    def step(self, dt: float) -> Dict:
        """Advance the whole system by dt seconds of simulated time:
        profile -> hardware (physics) -> BMS controller -> logging.
        Returns one sample of what happened. Used by the real-time thread and
        by run_for(), which needs no thread and is fully deterministic."""
        self.simulation_time += dt
        self._update_pack_current(dt)
        if isinstance(self.hardware, SimulationHardwareInterface):
            self.hardware.update_simulation(dt, self.target_pack_current)
        self.bms_controller.update(dt)
        self._acquire_and_log_data(dt)
        self._update_status_callbacks(dt)
        return self._sample()

    def _sample(self) -> Dict:
        status = self.bms_controller.get_status()
        sample = {
            "time": self.simulation_time,
            "requested_current": self.target_pack_current,
            "pack_current": status.pack_current * self.bms_controller.cells_in_parallel,
            "pack_voltage": status.pack_voltage,
            "soc_estimated": status.pack_soc,
            "max_temperature": status.pack_temperature,
            "state": status.state.value,
            "faults": list(dict.fromkeys(f.value for f in status.active_faults)),
            "balancing": status.balancing_active,
        }
        if isinstance(self.hardware, SimulationHardwareInterface):
            cells = self.hardware.cell_states
            sample["soc_true"] = float(np.mean([c["soc"] for c in cells]))
            sample["soc_true_cells"] = [c["soc"] for c in cells]
            sample["temperature_true_max"] = max(c["temperature"] for c in cells)
        return sample

    def run_for(self, duration: float, dt: float = 1.0) -> List[Dict]:
        """Run `duration` seconds of simulated time as fast as the CPU allows.
        Returns the list of samples, one per step."""
        return [self.step(dt) for _ in range(int(round(duration / dt)))]

    def _control_loop(self):
        """Real-time mode: step() paced by the wall clock in a thread."""
        last_loop_time = time.time()
        while self.control_loop_running:
            if self.simulation_paused:
                time.sleep(0.01)
                continue
            loop_start = time.time()
            dt = min(loop_start - last_loop_time, 0.1)      # never jump more than 100 ms
            last_loop_time = loop_start
            self.step(dt)
            sleep_time = max(0.0, self.time_step - (time.time() - loop_start))
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_pack_current(self, dt: float):
        """Update pack current based on charge/discharge profiles or target current."""
        if self.charge_discharge_simulator and self.charging_profile:
            # Use charging profile to calculate current
            bms_status = self.bms_controller.get_status()
            if bms_status:
                # Get cell voltage and SOC (use first cell or average)
                cell_voltages = self.hardware.read_all_cell_voltages()
                avg_voltage = np.mean(cell_voltages) if cell_voltages else 3.7

                # Calculate charging current from profile
                charging_result = self.charge_discharge_simulator.simulate_charging_step(
                    voltage=avg_voltage,
                    soc=bms_status.pack_soc,
                    temperature=bms_status.pack_temperature,
                    dt=dt,
                    nominal_capacity=self.pack_config.get("nominal_capacity", 50.0)
                )
                self.target_pack_current = charging_result["current"]

        elif self.charge_discharge_simulator and self.discharging_profile:
            # Use discharging profile to calculate current
            bms_status = self.bms_controller.get_status()
            if bms_status:
                cell_voltages = self.hardware.read_all_cell_voltages()
                avg_voltage = np.mean(cell_voltages) if cell_voltages else 3.7

                # Calculate discharging current from profile
                discharging_result = self.charge_discharge_simulator.simulate_discharging_step(
                    voltage=avg_voltage,
                    soc=bms_status.pack_soc,
                    time=self.simulation_time,
                    dt=dt,
                    nominal_capacity=self.pack_config.get("nominal_capacity", 50.0)
                )
                self.target_pack_current = discharging_result["current"]

        # Apply target current (it will be used in next hardware update)
        # The actual current flow depends on BMS controller state and protection

    def _acquire_and_log_data(self, dt: float):
        """Acquire data and log if enabled."""
        if not self.data_logger:
            return

        # Get BMS status
        bms_status = self.bms_controller.get_status()
        if not bms_status:
            return

        # Prepare data for logging
        log_data = {
            "time": self.simulation_time,
            "voltage": bms_status.pack_voltage,
            "current": bms_status.pack_current,
            "soc": bms_status.pack_soc,
            "soh": bms_status.pack_soh,
            "temperature": bms_status.pack_temperature,
            "power": bms_status.pack_voltage * bms_status.pack_current,
            "energy": 0.0  # Will be calculated cumulatively
        }

        # Log data (at configured interval)
        log_interval = self.simulation_config.get("logging", {}).get("log_interval", 1.0)
        if int(self.simulation_time / log_interval) != int((self.simulation_time - dt) / log_interval):
            self.data_logger.log(log_data)

    def _update_status_callbacks(self, dt: float):
        """Update status callbacks at specified frequency."""
        current_time = time.time()
        if current_time - self.last_status_update >= self.status_update_interval:
            bms_status = self.bms_controller.get_status()
            if bms_status:
                for callback in self.status_callbacks:
                    callback(bms_status)
            self.last_status_update = current_time

    def _on_state_change(self, old_state, new_state):
        """Log state changes (logging, not print: library code stays quiet
        unless the application turns logging on)."""
        log.info("BMS state %s -> %s at t=%.1f s", old_state.value, new_state.value, self.simulation_time)

    def _on_fault(self, faults, level):
        """Log a fault when the set of active faults changes, not on every
        tick it stays active; callbacks still see every report."""
        key = (tuple(dict.fromkeys(f.value for f in faults)), level.value)
        if key != self._last_fault_key:
            log.warning("BMS %s: %s at t=%.1f s", level.value, ", ".join(key[0]), self.simulation_time)
            self._last_fault_key = key
        for callback in self.fault_callbacks:
            callback(faults, level)

    def get_status(self):
        """Get current simulation status."""
        bms_status = self.bms_controller.get_status()
        return {
            "simulation_time": self.simulation_time,
            "simulation_running": self.simulation_running,
            "simulation_paused": self.simulation_paused,
            "bms_status": bms_status,
            "hardware_info": self.hardware.get_hardware_info(),
            "statistics": self.bms_controller.get_statistics()
        }

    def register_status_callback(self, callback: Callable):
        """Register callback for status updates."""
        self.status_callbacks.append(callback)

    def register_fault_callback(self, callback: Callable):
        """Register callback for fault events."""
        self.fault_callbacks.append(callback)

