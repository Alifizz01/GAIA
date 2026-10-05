"""The real-time BMS: physics bookkeeping and every protection path."""
import pytest

from gaia import (BatteryBalancer, BalancingMethod, BatteryPack, SimulationEngine,
                  SimulationHardwareInterface)


def engine(**over):
    pack = {"cells_in_series": 8, "cells_in_parallel": 1, "nominal_capacity": 50.0, "chemistry": "NMC",
            "sensor_noise": False, "seed": 1, **over}
    e = SimulationEngine(SimulationHardwareInterface(pack), pack, simulation_config={"logging": {"enabled": False}})
    assert e.initialize()
    return e


def test_half_an_hour_at_1c_uses_half_the_charge():
    e = engine()
    e.set_pack_current(50.0)
    s = e.run_for(1800)[-1]
    assert s["soc_true"] == pytest.approx(50.0, abs=0.2)
    assert s["soc_estimated"] == pytest.approx(s["soc_true"], abs=1.0)
    assert s["temperature_true_max"] - 273.15 < 45                 # Kelvin end to end, not 573 K
    wh = e.bms_controller.total_energy_discharged
    assert 8 * 3.6 * 25 < wh < 8 * 4.2 * 25                        # 8 cells x ~3.8 V x 25 Ah


def test_no_current_flows_without_permission():
    e = engine()
    e.set_pack_current(0.0)
    e.target_pack_current = 50.0                  # requested, but discharge never permitted
    assert all(s["pack_current"] == 0.0 for s in e.run_for(5))


@pytest.mark.parametrize("current, fault", [(150.0, "overcurrent_discharge"), (-80.0, "overcurrent_charge")])
def test_overcurrent_trips_and_opens_the_contactor(current, fault):
    e = engine(initial_soc=50.0)
    e.set_pack_current(current)
    samples = e.run_for(3, 0.1)
    assert fault in samples[-1]["faults"]
    assert samples[-1]["pack_current"] == 0.0
    assert samples[-1]["state"] == "fault"


def test_a_load_step_is_not_a_short_circuit():
    """Regression: the rise rate assumed a 100 ms tick, so 0 -> 101 A tripped EMERGENCY."""
    e = engine()
    e.set_pack_current(95.0)
    s = e.run_for(2, 0.01)[-1]
    assert s["faults"] == [] and s["pack_current"] == pytest.approx(95.0)


def test_overtemperature_latches_until_the_cell_cools():
    e = engine()
    e.set_pack_current(25.0)
    e.run_for(5)
    e.hardware.set_cell_state(3, {"temperature": 273.15 + 65})
    s = e.run_for(2)[-1]
    assert "overtemperature" in s["faults"] and s["pack_current"] == 0.0
    assert e.bms_controller.reset_fault() is False                  # still hot: stays latched
    e.hardware.set_cell_state(3, {"temperature": 273.15 + 30})
    e.run_for(2)
    assert e.bms_controller.reset_fault() is True
    e.set_pack_current(25.0)
    assert e.run_for(2)[-1]["pack_current"] == pytest.approx(25.0)


def test_over_discharge_trips_undervoltage():
    e = engine(initial_soc=3.0)
    e.set_pack_current(50.0)
    samples = e.run_for(600)
    trip = next(s for s in samples if s["faults"])
    assert "undervoltage" in trip["faults"]
    assert samples[-1]["pack_current"] == 0.0


def test_over_charge_trips_overvoltage():
    e = engine(initial_soc=99.0)
    e.set_pack_current(-25.0)
    samples = e.run_for(900)
    assert any("overvoltage" in s["faults"] for s in samples)
    assert samples[-1]["pack_current"] == 0.0


def test_balancing_bleeds_the_high_cells():
    e = engine(cell_variation={"soc": 3.0}, initial_soc=70.0)
    e.set_pack_current(0.0)
    samples = e.run_for(6 * 3600, 10.0)
    spread = [max(s["soc_true_cells"]) - min(s["soc_true_cells"]) for s in (samples[0], samples[-1])]
    assert samples[0]["balancing"]
    assert spread[1] < spread[0] - 0.5


def test_internal_short_drains_one_cell():
    e = engine(initial_soc=60.0)
    e.hardware.set_cell_state(2, {"leak_current": 10.0})
    e.set_pack_current(0.0)
    s = e.run_for(1800)[-1]
    cells = s["soc_true_cells"]
    assert cells[2] < min(c for i, c in enumerate(cells) if i != 2) - 5


def test_soc_filter_recovers_from_a_wrong_start_and_coulomb_counting_does_not():
    err = {}
    for method in ("COULOMB_COUNTING", "AEKF"):
        e = SimulationEngine(*(lambda p: (SimulationHardwareInterface(p), p))(
            {"cells_in_series": 4, "nominal_capacity": 50.0, "chemistry": "NMC", "seed": 2}),
            bms_config={"soc_estimation": {"method": method}}, simulation_config={"logging": {"enabled": False}})
        e.initialize()
        for est in e.bms_controller.soc_estimators:
            if method == "AEKF":
                est.estimator.x[0] = 0.80
            else:
                est.reset(80.0)
        e.set_pack_current(25.0)
        s = e.run_for(1200)[-1]
        err[method] = abs(s["soc_estimated"] - s["soc_true"])
    assert err["COULOMB_COUNTING"] > 15
    assert err["AEKF"] < 2


def test_passive_balancer_targets_the_lowest_cell():
    """Regression: it compared against the average and never acted on one low cell."""
    pack = BatteryPack(cells_in_series=8, cells_in_parallel=1, chemistry="NMC")
    pack.update_cell_state(3, 0, voltage=3.7, soc=92.0, temperature=298.15, current=0.0)
    result = BatteryBalancer(method=BalancingMethod.PASSIVE, balancing_threshold=0.02).balance(pack, dt=1.0)
    assert result["active_cells"] == 7
