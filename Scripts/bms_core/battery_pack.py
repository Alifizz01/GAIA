import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # Ensure correct module import
from bms_core.battery_cell import Cell,   # type: ignore

class BatteryPack:
    def __init__(self, series_number=5, parallel_number=5, chemistry="NCA"):
        """Initialize Battery Pack with multiple cells."""
        
        self.chemistry = chemistry  # Store the selected chemistry
        self.series_number = series_number
        self.parallel_number = parallel_number

        # ✅ Use dynamically loaded chemistry properties for cells
        self.cells = [
            [Cell(chemistry=self.chemistry) for _ in range(parallel_number)]
            for _ in range(series_number)
        ]

    def total_voltage(self):
        """Total pack voltage is based on series cells."""
        return self.cells[0][0].nominal_voltage * self.series_number

    def total_capacity(self):
        """Total pack capacity is based on parallel cells."""
        return self.cells[0][0].nominal_capacity * self.parallel_number

    def total_internal_resistance(self):
        """Calculate total internal resistance (series resistance increases)."""
        return self.cells[0][0].internal_resistance * self.series_number

    def out_current(self, input_current):
        """Output current is shared among parallel cells."""
        return input_current / self.parallel_number if self.parallel_number > 0 else input_current

    def total_soc(self):
        """Calculate average SOC across all series cells."""
        return sum(series[0].soc for series in self.cells) / self.series_number

    def update_pack_soc(self, measured_voltage, current, dt):
        """Update SOC for all cells in the battery pack."""
        for series in self.cells:
            for cell in series:
                cell.update_soc(measured_voltage, current, dt)

    def balance_cells(self):
        """Simple passive balancing: reduce SOC of highest cell."""
        avg_soc = sum(series[0].soc for series in self.cells) / self.series_number
        for series in self.cells:
            for cell in series:
                if cell.soc > avg_soc + 1.0:
                    cell.soc -= 0.1

    def display_pack_info(self):
        """Prints overall battery pack information."""
        print("Battery Pack Chemistry: NMC") if self.chemistry is None else print(f"Battery Pack Chemistry: {self.chemistry}")
        print(f"Total Voltage: {self.total_voltage()}V")
        print(f"Total Capacity: {self.total_capacity()}Ah")
        print(f"Total Internal Resistance: {self.total_internal_resistance()} mΩ")
        print(f"Total SOC: {self.total_soc():.2f}%")

# ✅ Fix: Create an instance before calling `display_pack_info`
pack = BatteryPack()
pack.display_pack_info()  # ✅ Corrected method call
