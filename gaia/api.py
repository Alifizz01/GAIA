"""Everything GAIA Studio can do, as plain functions: dict in, dict out.

server.py exposes each entry of ROUTES as POST /api/<name>. The live pack is
one SimulationEngine stepped in simulated time; the browser asks for the
next few seconds every frame, so nothing runs in a background thread and a
run is reproducible.
"""
from __future__ import annotations

import threading

import numpy as np

import gaia

STATE: dict = {}
LOCK = threading.Lock()


def _thin(arr, n=600):
    arr = np.asarray(arr)
    step = max(1, int(np.ceil(len(arr) / n)))
    return arr[::step].tolist()


def info(_=None):
    from .ocv import CHEMISTRIES
    return {"version": gaia.__version__, "chemistries": list(CHEMISTRIES),
            "models": ["SPM", "SPMe", "DFN"], "faults": list(FAULTS)}


# ------------------------------------------------------------------ live pack
DEFAULT_PACK = {"cells_in_series": 12, "cells_in_parallel": 1, "nominal_capacity": 50.0,
                "chemistry": "NMC", "initial_soc": 80.0, "ambient_temperature": 298.15,
                "cell_variation": {"capacity": 0.02, "soc": 1.5, "resistance": 0.05}, "seed": 3}


def pack_reset(body=None):
    from .hardware_interface import SimulationHardwareInterface
    from .simulation_engine import SimulationEngine
    cfg = {**DEFAULT_PACK, **(body or {})}
    cfg["cells_in_series"] = int(np.clip(cfg["cells_in_series"], 1, 24))
    engine = SimulationEngine(SimulationHardwareInterface(cfg), cfg, simulation_config={"logging": {"enabled": False}})
    engine.initialize()
    STATE["pack"] = {"engine": engine, "config": cfg, "history": [], "events": []}
    engine.bms_controller.register_state_change_callback(
        lambda old, new: _event(f"state {old.value} -> {new.value}"))
    engine.register_fault_callback(lambda faults, level: None)
    engine.step(0.1)
    return pack_state()


def _pack():
    if "pack" not in STATE:
        pack_reset()
    return STATE["pack"]


def _event(text):
    pack = STATE.get("pack")
    if pack is not None:
        t = pack["engine"].simulation_time
        if not pack["events"] or pack["events"][-1]["text"] != text:
            pack["events"].append({"t": round(t, 1), "text": text})
            pack["events"] = pack["events"][-40:]


def pack_command(body):
    """current in A (positive = discharge, negative = charge, 0 = rest)."""
    engine = _pack()["engine"]
    engine.set_pack_current(float(body.get("current", 0.0)))
    if "ambient" in body:
        engine.hardware.ambient_temperature = float(body["ambient"])
    return pack_state()


def pack_step(body):
    """Advance the pack by `seconds` of simulated time in 1 s steps."""
    pack = _pack()
    engine = pack["engine"]
    seconds = float(np.clip(body.get("seconds", 1.0), 0.1, 600.0))
    steps = max(1, int(round(seconds)))
    dt = seconds / steps
    faults_before = set(engine.bms_controller.latched_faults)
    for _ in range(steps):
        s = engine.step(dt)
        pack["history"].append({k: s[k] for k in ("time", "pack_current", "pack_voltage", "soc_estimated",
                                                  "soc_true", "temperature_true_max")})
    pack["history"] = pack["history"][-4000:]
    new = set(engine.bms_controller.latched_faults) - faults_before
    if new:
        _event("TRIP: " + ", ".join(sorted(f.value for f in new)))
    return pack_state()


def pack_state(_=None):
    pack = _pack()
    engine = pack["engine"]
    ctrl, hw = engine.bms_controller, engine.hardware
    status = ctrl.get_status()
    est = [c.soc for group in ctrl.battery_pack.cells for c in group]
    cells = [{"id": i, "soc": c["soc"], "soc_est": est[i], "voltage": c["voltage"],
              "temperature": c["temperature"] - 273.15, "bleeding": bool(hw.balancing_enabled.get(i)),
              "leak": c.get("leak_current", 0.0) > 0, "capacity": c["capacity"]}
             for i, c in enumerate(hw.cell_states)]
    h = pack["history"]
    return {
        "time": engine.simulation_time,
        "config": {k: v for k, v in pack["config"].items() if k != "cell_variation"},
        "state": ctrl.state.value,
        "requested_current": engine.target_pack_current,
        "pack_current": hw.pack_current,
        "pack_voltage": sum(c["voltage"] for c in hw.cell_states) / hw.cells_in_parallel,
        "soc_estimated": status.pack_soc,
        "soc_true": float(np.mean([c["soc"] for c in hw.cell_states])),
        "charge_contactor": hw.charge_enabled, "discharge_contactor": hw.discharge_enabled,
        "ambient_c": hw.ambient_temperature - 273.15,
        "faults": list(dict.fromkeys(f.value for f in status.active_faults)),
        "latched": [f.value for f in ctrl.latched_faults],
        "energy_out_wh": ctrl.total_energy_discharged, "energy_in_wh": ctrl.total_energy_charged,
        "cells": cells,
        "history": {k: _thin([x[k] for x in h]) for k in (h[0].keys() if h else [])},
        "events": pack["events"][-12:],
    }


FAULTS = {
    "overheat": "cell heats to 65 C (cooling fault next to it)",
    "short": "internal short: the cell drains at C/5 on its own",
    "fade": "capacity fades to 70 % (an aged cell)",
    "heal": "remove the fault and cool the cell",
}


def pack_fault(body):
    hw = _pack()["engine"].hardware
    cid, kind = int(body["cell"]), body["kind"]
    cell = hw.cell_states[cid]
    if kind == "overheat":
        hw.set_cell_state(cid, {"temperature": 273.15 + 65.0})
    elif kind == "short":
        hw.set_cell_state(cid, {"leak_current": cell["capacity"] / 5})
    elif kind == "fade":
        hw.set_cell_state(cid, {"capacity": cell["capacity"] * 0.7})
    elif kind == "heal":
        hw.set_cell_state(cid, {"leak_current": 0.0, "temperature": hw.ambient_temperature})
    else:
        raise ValueError(f"unknown fault {kind!r}: {list(FAULTS)}")
    _event(f"inject {kind} on cell {cid + 1}")
    return pack_state()


def pack_reset_fault(_=None):
    ok = _pack()["engine"].bms_controller.reset_fault()
    _event("fault reset accepted" if ok else "fault reset refused: condition still present")
    return {**pack_state(), "reset_accepted": ok}


# ------------------------------------------------------------------ cell lab (PyBaMM)
def cell_simulate(body):
    from .simulation_manager import SimulatorManager
    chem = body.get("chemistry", "NMC")
    c_rate = float(body.get("c_rate", 1.0))
    duration = int(np.clip(float(body.get("duration", 3600 / max(abs(c_rate), 0.05))), 60, 90000))
    sim = SimulatorManager(body.get("model", "SPM"), chem, 273.15 + float(body.get("temperature_c", 25.0)),
                           c_rate=c_rate, thermal="lumped" if body.get("thermal") else "isothermal")
    sim.run_battery_simulation(duration)
    t, v, soc, temp, i = sim.get_simulation_results()
    keep = np.asarray(v) > 0
    return {"label": f"{chem} {body.get('model', 'SPM')} {c_rate:g}C" + (" thermal" if body.get("thermal") else ""),
            "capacity": sim.battery_model.parameter_values["Nominal cell capacity [A.h]"],
            "t": _thin(np.asarray(t)[keep]), "voltage": _thin(np.asarray(v)[keep]), "soc": _thin(np.asarray(soc)[keep]),
            "temperature": _thin(np.asarray(temp)[keep] - 273.15), "current": _thin(np.asarray(i)[keep])}


# ------------------------------------------------------------------ SOC lab
def soc_benchmark(body):
    from .soc_benchmark import run_benchmark
    r = run_benchmark(body.get("chemistry", "NMC"), duration=float(body.get("duration", 2700)),
                      initial_soc_guess=float(body.get("initial_soc_guess", 80.0)),
                      voltage_noise=float(body.get("voltage_noise", 0.005)),
                      current_offset=float(body.get("current_offset", 0.01)))
    return {"chemistry": r["chemistry"], "capacity": r["capacity"], "t": _thin(r["t"]),
            "soc_true": _thin(r["soc_true"]), "current": _thin(r["current"]), "voltage": _thin(r["voltage"]),
            "estimates": {k: _thin(v) for k, v in r["estimates"].items()},
            "rmse_after_10min": r["rmse_after_10min"], "final_error": r["final_error"],
            "conditions": r["conditions"]}


ROUTES = {f.__name__: f for f in (info, pack_reset, pack_command, pack_step, pack_state, pack_fault,
                                  pack_reset_fault, cell_simulate, soc_benchmark)}
