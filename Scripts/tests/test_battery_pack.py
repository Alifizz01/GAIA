import sys
import os

sys.path.append(os.path.abspath("../"))

import unittest
from bms_core.battery_pack import BatteryPack # type: ignore

class TestBatteryPack(unittest.TestCase):
    def test_battery_pack_values(self):
        battery_pack = BatteryPack(series_number=4, parallel_number=2)

        final_voltage = battery_pack.total_voltage()
        final_current = battery_pack.out_current(input_current=1)
        total_capacity = battery_pack.total_capacity()

        self.assertAlmostEqual(final_voltage, 14.8, places=2, msg=f"Expected 14.8V, got {final_voltage}V")
        self.assertAlmostEqual(total_capacity, 6.8, places=2, msg=f"Expected 6.8Ah, got {total_capacity}Ah")
        self.assertAlmostEqual(final_current, 0.5, places=2, msg=f"Expected 0.5A, got {final_current}A")

if __name__ == "__main__":
    unittest.main()


