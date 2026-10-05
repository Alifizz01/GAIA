"""GAIA as a XiLoop plant: a CC-CV charger verified closed-loop."""
import os

import pytest

xiloop = pytest.importorskip("xiloop")

PLAN = os.path.join(os.path.dirname(__file__), "..", "examples", "xiloop_cccv", "testplan.yaml")


def test_tuned_cccv_charger_passes_its_requirements():
    from xiloop.campaign import CampaignRunner, load_plan
    plan = load_plan(PLAN)
    result = CampaignRunner.from_plan(plan).run(plan)
    assert result.passed, result.summary()


def test_unstable_gains_are_caught():
    from xiloop.campaign import CampaignRunner, load_plan
    plan = load_plan(PLAN)
    plan["device"]["params"].update(kp=100.0, ki=20.0)
    result = CampaignRunner.from_plan(plan).run(plan)
    failed = [r.req_id for rs in result.scenario_results.values() for r in rs if not r.passed]
    assert failed == ["REQ-CV-2"]


def test_charger_goes_from_constant_current_to_constant_voltage():
    from xiloop import PID, PIDDevice, LoopEngine
    from gaia.xiloop_plant import GaiaCellPlant
    plant = GaiaCellPlant(capacity=5.0, initial_soc=20.0)
    run = LoopEngine(PIDDevice(PID(kp=50, ki=5, kd=0, out_max=5.0)), plant).run(setpoint=4.1, duration=7200, dt=1.0)
    assert run.command[60] == pytest.approx(5.0)          # CC phase: saturated at 1C
    assert run.command[-1] < 0.1                          # CV phase tapers to nothing
    assert plant.soc > 85
