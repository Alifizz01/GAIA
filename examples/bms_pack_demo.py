"""A 16s1p NMC pack under BMS control: discharge, a hot cell, the trip, the reset.

    python examples/bms_pack_demo.py

Runs in simulated time (a few seconds of CPU for an hour of battery), with the
same engine Studio uses. Every number printed is read back from the BMS.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gaia import SimulationEngine, SimulationHardwareInterface  # noqa: E402

PACK = {
    "cells_in_series": 16, "cells_in_parallel": 1, "nominal_capacity": 50.0, "chemistry": "NMC",
    "initial_soc": 90.0, "cell_variation": {"capacity": 0.01, "soc": 1.0}, "seed": 7,
}


def show(label, sample):
    print(f"{label:<34} t={sample['time']:>6.0f} s  I={sample['pack_current']:>6.1f} A  "
          f"V={sample['pack_voltage']:>5.1f} V  SOC est/true={sample['soc_estimated']:>5.1f}/{sample['soc_true']:>5.1f} %  "
          f"Tmax={sample['temperature_true_max'] - 273.15:>5.1f} C  {sample['state']} {sample['faults'] or ''}")


def main():
    engine = SimulationEngine(SimulationHardwareInterface(PACK), PACK,
                              simulation_config={"logging": {"enabled": False}})
    engine.initialize()

    engine.set_pack_current(50.0)                       # 1C discharge
    show("30 min at 1C", engine.run_for(1800)[-1])

    engine.hardware.set_cell_state(7, {"temperature": 273.15 + 64})   # cell 7 overheats
    show("cell 7 at 64 C", engine.run_for(2)[-1])
    print(f"{'reset while still hot':<34} accepted={engine.bms_controller.reset_fault()}")

    engine.hardware.set_cell_state(7, {"temperature": 273.15 + 30})   # it cools down
    engine.run_for(2)
    print(f"{'reset after cooling':<34} accepted={engine.bms_controller.reset_fault()}")

    engine.set_pack_current(50.0)
    show("discharge until empty", engine.run_for(3600)[-1])
    stats = engine.bms_controller.get_statistics()
    print(f"\nenergy delivered: {stats['total_energy_discharged_wh']:.0f} Wh")


if __name__ == "__main__":
    main()
