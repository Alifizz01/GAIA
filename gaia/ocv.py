"""Open-circuit voltage (OCV) as a function of state of charge, per chemistry.

The tables in gaia/data/ocv_<chemistry>.csv come from GAIA's own PyBaMM
model: a C/25 discharge is slow enough that the terminal voltage sits within
a few millivolts of the true OCV. Using the same physics for the real-time
cell model and for the SOC filters is what lets the two be compared fairly.

    python -m gaia.ocv                # regenerate the tables (needs PyBaMM)
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CHEMISTRIES = ("NMC", "LFP", "NCA")


class OCVCurve:
    """Monotonic OCV(SOC) lookup with its inverse and slope. SOC in 0..100 %."""

    def __init__(self, soc: np.ndarray, ocv: np.ndarray, chemistry: str = ""):
        order = np.argsort(soc)
        self.soc = np.asarray(soc, dtype=float)[order]
        # enforce strictly increasing OCV so the inverse is well defined
        self.v = np.maximum.accumulate(np.asarray(ocv, dtype=float)[order]) + np.linspace(0, 1e-6, len(order))
        self.chemistry = chemistry

    def ocv(self, soc):
        return np.interp(soc, self.soc, self.v)

    def soc_from_ocv(self, v):
        return np.interp(v, self.v, self.soc)

    def slope(self, soc, h: float = 0.5):
        """dOCV/dSOC in V per % SOC."""
        return (self.ocv(np.clip(soc + h, 0, 100)) - self.ocv(np.clip(soc - h, 0, 100))) / (2 * h)

    @property
    def v_min(self) -> float:
        return float(self.v[0])

    @property
    def v_max(self) -> float:
        return float(self.v[-1])


@lru_cache(maxsize=None)
def ocv_curve(chemistry: str = "NMC") -> OCVCurve:
    path = os.path.join(DATA, f"ocv_{chemistry.lower()}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no OCV table for {chemistry!r}: available {list(CHEMISTRIES)}")
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return OCVCurve(data[:, 0], data[:, 1], chemistry)


def generate(chemistry: str, points: int = 201) -> None:
    """Pseudo-OCV from a C/25 PyBaMM discharge, resampled on a fixed SOC grid."""
    from .battery_model import BatteryModel
    bm = BatteryModel("SPMe", chemistry)
    cap = bm.parameter_values["Nominal cell capacity [A.h]"]
    bm.change_parameters("Current function [A]", cap / 25)
    sol = bm.run_simulation(duration=25 * 3600)
    soc = 100 * (1 - sol["Discharge capacity [A.h]"].entries / cap)
    v = sol["Voltage [V]"].entries
    grid = np.linspace(max(soc.min(), 0), min(soc.max(), 100), points)
    curve = np.interp(grid, soc[::-1], v[::-1])
    os.makedirs(DATA, exist_ok=True)
    np.savetxt(os.path.join(DATA, f"ocv_{chemistry.lower()}.csv"), np.column_stack([grid, curve]),
               delimiter=",", header="soc_percent,ocv_volt", comments="", fmt="%.6f")


if __name__ == "__main__":
    for chem in CHEMISTRIES:
        generate(chem)
        c = ocv_curve.__wrapped__(chem)
        print(f"{chem}: {c.soc[0]:.1f}..{c.soc[-1]:.1f} % -> {c.v_min:.3f}..{c.v_max:.3f} V")
