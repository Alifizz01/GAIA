"""The PyBaMM cell model: physics sanity, not exact numbers."""
import numpy as np
import pytest

from gaia import SimulatorManager
from gaia.ocv import CHEMISTRIES, ocv_curve


@pytest.mark.parametrize("chemistry", CHEMISTRIES)
def test_one_hour_at_1c_empties_the_cell(chemistry):
    sim = SimulatorManager("SPM", chemistry, 298.15)
    sim.run_battery_simulation(3600)
    t, v, soc, temp, current = sim.get_simulation_results()
    assert soc[0] == pytest.approx(100, abs=0.5)
    assert soc[-1] < 3                              # 1C for an hour drains a cell
    assert np.all(np.diff(soc) <= 1e-9)             # discharge never adds charge
    assert 2.5 < v[-1] < v[0] < 4.3


def test_output_is_smooth_not_piecewise_linear():
    """Regression: solving on [0, T] only returned a handful of points."""
    sim = SimulatorManager("SPM", "NMC", 298.15)
    sim.run_battery_simulation(3600)
    _, v, *_ = sim.get_simulation_results()
    second_diff = np.abs(np.diff(v, 2))
    assert second_diff.max() < 0.01                 # no kinks between sparse solver steps


def test_lumped_thermal_heats_and_isothermal_does_not():
    temps = {}
    for thermal in ("isothermal", "lumped"):
        sim = SimulatorManager("SPMe", "NMC", 298.15, c_rate=2.0, thermal=thermal)
        sim.run_battery_simulation(1500)
        temps[thermal] = max(sim.get_simulation_results()[3]) - 298.15
    assert temps["isothermal"] == pytest.approx(0, abs=1e-6)
    assert temps["lumped"] > 3


def test_higher_c_rate_means_lower_voltage():
    end_v = {}
    for rate in (0.5, 2.0):
        sim = SimulatorManager("SPMe", "NMC", 298.15, c_rate=rate)
        sim.run_battery_simulation(600)
        end_v[rate] = sim.get_simulation_results()[1][-1]
    assert end_v[2.0] < end_v[0.5]


@pytest.mark.parametrize("chemistry", CHEMISTRIES)
def test_ocv_tables_are_monotonic_and_invertible(chemistry):
    curve = ocv_curve(chemistry)
    assert np.all(np.diff(curve.v) > 0)
    for soc in (5, 30, 50, 80, 95):
        assert curve.soc_from_ocv(curve.ocv(soc)) == pytest.approx(soc, abs=0.1)


def test_lfp_is_flat_where_nmc_is_not():
    """Why voltage-based SOC is hard on LFP."""
    span = {c: ocv_curve(c).ocv(80) - ocv_curve(c).ocv(30) for c in ("LFP", "NMC")}
    assert span["LFP"] < 0.1 < span["NMC"]
