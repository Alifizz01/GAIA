#!/usr/bin/env python3
"""
GAIA Simulation Runner — Python bridge for the Rust GUI.

Usage:
    python3 run_simulation.py --params '<JSON>'

Output:
    Any lines from PyBaMM/logging go to stdout normally.
    The final result is emitted as one line:
        GAIA_RESULT:{...json...}

    The Rust frontend scans stdout for the GAIA_RESULT: prefix.
"""

import sys
import json
import os
import argparse

# Make sure bms_core is importable from this file's directory
_SCRIPTS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, _SCRIPTS_DIR)


def _to_list(arr):
    """Convert numpy array or list to plain Python list."""
    if hasattr(arr, "tolist"):
        return arr.tolist()
    return list(arr)


def run_simulation(params: dict) -> dict:
    try:
        from bms_core.simulation_manager import SimulatorManager

        model_type = params.get("model_type", "SPM")
        chemistry = params.get("chemistry", "NMC")
        initial_temperature = float(params.get("initial_temperature", 298.15))
        duration = int(params.get("duration", 3600))

        sim = SimulatorManager(model_type, chemistry, initial_temperature)
        sim.run_battery_simulation(duration)

        time_data, voltage_data, soc_data, temp_data, current_data = (
            sim.get_simulation_results()
        )

        return {
            "success": True,
            "time": _to_list(time_data),
            "voltage": _to_list(voltage_data),
            "soc": _to_list(soc_data),
            "temperature": _to_list(temp_data),
            "current": _to_list(current_data),
            "error": None,
        }

    except Exception as exc:  # noqa: BLE001
        import traceback
        return {
            "success": False,
            "time": [],
            "voltage": [],
            "soc": [],
            "temperature": [],
            "current": [],
            "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="GAIA simulation runner")
    parser.add_argument(
        "--params",
        required=True,
        help="JSON string with simulation parameters",
    )
    args = parser.parse_args()

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as exc:
        result = {
            "success": False,
            "time": [], "voltage": [], "soc": [],
            "temperature": [], "current": [],
            "error": f"Invalid JSON in --params: {exc}",
        }
        print(f"GAIA_RESULT:{json.dumps(result)}", flush=True)
        sys.exit(1)

    result = run_simulation(params)
    # Flush any buffered PyBaMM output first so the marker line is last.
    sys.stdout.flush()
    print(f"GAIA_RESULT:{json.dumps(result)}", flush=True)


if __name__ == "__main__":
    main()
