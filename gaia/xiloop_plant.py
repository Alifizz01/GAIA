"""A GAIA cell as a XiLoop plant: test battery controllers closed-loop.

XiLoop (github.com/Alifizz01/XiLoop) wires a controller to a plant and checks
requirements. This plant is one GAIA cell (OCV table from PyBaMM, R0 + RC,
lumped thermal mass):

    command     = charge current [A]   (positive charges the cell)
    measurement = terminal voltage [V]

So a XiLoop PID with out_max = the charge current limit, regulating the
voltage to 4.1 V, is a CC-CV charger: saturated (constant current) while the
voltage is low, regulating (constant voltage) near the target. See
examples/xiloop_cccv/ for a test plan with safety requirements.

Requires `pip install xiloop`; GAIA does not depend on it otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass

from xiloop import Plant

from .hardware_interface import SimulationHardwareInterface


@dataclass
class GaiaCellPlant(Plant):
    STATE = ("_hw",)
    chemistry: str = "NMC"
    capacity: float = 5.0          # Ah
    initial_soc: float = 20.0      # %
    ambient_c: float = 25.0
    _hw: SimulationHardwareInterface | None = None

    def reset(self) -> None:
        cfg = {"cells_in_series": 1, "nominal_capacity": self.capacity, "chemistry": self.chemistry,
               "initial_soc": self.initial_soc, "ambient_temperature": 273.15 + self.ambient_c,
               "sensor_noise": False}
        self._hw = SimulationHardwareInterface(cfg)
        self._hw.initialize()
        self._hw.enable_charge(True)
        self._hw.enable_discharge(True)

    def step(self, command: float, dt: float) -> float:
        if self._hw is None:
            self.reset()
        self._hw.update_simulation(dt, -command)          # GAIA: positive = discharge
        return self._hw.cell_states[0]["voltage"]

    @property
    def soc(self) -> float:
        return self._hw.cell_states[0]["soc"] if self._hw else self.initial_soc
