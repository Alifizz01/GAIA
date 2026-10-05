"""A MATLAB/Simulink-friendly face of the GAIA BMS engine.

MATLAB's Python interface converts floats, ints, strings and lists of
numbers cleanly; nested dicts of numpy arrays not so much. Everything here
returns those simple types, so the MATLAB wrappers in matlab/ stay short.

    pack = MatlabPack(12, "NMC", 50.0, 80.0)
    pack.set_current(50.0)
    y = pack.step(1.0)        # [V, I, SOC_est, SOC_true, Tmax_C, state, dsg, chg, fault]
"""
from __future__ import annotations

from .hardware_interface import SimulationHardwareInterface
from .simulation_engine import SimulationEngine

STATES = ["idle", "charging", "discharging", "balancing", "fault", "emergency", "maintenance"]
OUTPUTS = ["pack_voltage_V", "pack_current_A", "soc_estimated_pct", "soc_true_pct", "max_temperature_C",
           "bms_state", "discharge_contactor", "charge_contactor", "fault_latched"]


class MatlabPack:
    def __init__(self, cells_in_series: float = 12, chemistry: str = "NMC", capacity_ah: float = 50.0,
                 initial_soc: float = 80.0, ambient_c: float = 25.0, seed: float = 1, sensor_noise: bool = True):
        cfg = {"cells_in_series": int(cells_in_series), "cells_in_parallel": 1, "chemistry": str(chemistry),
               "nominal_capacity": float(capacity_ah), "initial_soc": float(initial_soc),
               "ambient_temperature": 273.15 + float(ambient_c), "seed": int(seed),
               "sensor_noise": bool(sensor_noise), "cell_variation": {"capacity": 0.02, "soc": 1.0}}
        self.engine = SimulationEngine(SimulationHardwareInterface(cfg), cfg,
                                       simulation_config={"logging": {"enabled": False}})
        self.engine.initialize()

    def set_current(self, amps: float) -> None:
        """Requested pack current in A: positive = discharge, negative = charge."""
        self.engine.set_pack_current(float(amps))

    def step(self, dt: float = 1.0) -> list:
        """Advance dt seconds; returns the values named in OUTPUTS (all numbers)."""
        s = self.engine.step(float(dt))
        ctrl = self.engine.bms_controller
        return [float(s["pack_voltage"]), float(self.engine.hardware.pack_current), float(s["soc_estimated"]),
                float(s["soc_true"]), float(s["temperature_true_max"] - 273.15), float(STATES.index(s["state"])),
                float(self.engine.hardware.discharge_enabled), float(self.engine.hardware.charge_enabled),
                float(bool(ctrl.latched_faults))]

    def run_for(self, seconds: float, dt: float = 1.0) -> dict:
        """Run with the current request; returns {name: list} per OUTPUTS plus time_s."""
        rows = [self.step(dt) for _ in range(int(round(float(seconds) / float(dt))))]
        out = {name: [r[k] for r in rows] for k, name in enumerate(OUTPUTS)}
        out["time_s"] = [float(self.engine.simulation_time - (len(rows) - 1 - k) * float(dt)) for k in range(len(rows))]
        return out

    def cell_soc(self) -> list:
        return [float(c["soc"]) for c in self.engine.hardware.cell_states]

    def cell_temperature_c(self) -> list:
        return [float(c["temperature"] - 273.15) for c in self.engine.hardware.cell_states]

    def inject_fault(self, cell: float, kind: str) -> None:
        """kind: overheat | short | fade | heal (cell is 1-based, as in MATLAB)."""
        from .api import FAULTS
        hw, cid = self.engine.hardware, int(cell) - 1
        c = hw.cell_states[cid]
        changes = {"overheat": {"temperature": 273.15 + 65.0}, "short": {"leak_current": c["capacity"] / 5},
                   "fade": {"capacity": c["capacity"] * 0.7},
                   "heal": {"leak_current": 0.0, "temperature": hw.ambient_temperature}}
        if kind not in changes:
            raise ValueError(f"unknown fault {kind!r}: {list(FAULTS)}")
        hw.set_cell_state(cid, changes[kind])

    def reset_fault(self) -> bool:
        return bool(self.engine.bms_controller.reset_fault())

    def faults(self) -> list:
        return [f.value for f in self.engine.bms_controller.latched_faults]
