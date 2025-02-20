import os
import sys

sys.path.append(os.path.abspath("../"))  # Ensure correct module import

from bms_core.battery_cell import Cell  # type: ignore 

class BatteryPack:
    def __init__(self, series_number=1, parallel_number=1):
        """Initialize Battery Pack with multiple cells."""
        self.series_number = series_number
        self.parallel_number = parallel_number

        # Create a matrix of Cell objects [series][parallel]
        self.cells = [[Cell(capacity=3.4, nominal_voltage=3.7, internal_resistance=0.005) 
                      for _ in range(parallel_number)] for _ in range(series_number)]

    def total_voltage(self):
        """Total pack voltage is based on series cells."""
        return self.cells[0][0].nominal_voltage * self.series_number  # Use the first cell's voltage

    def total_capacity(self):
        """Total pack capacity is based on parallel cells."""
        return self.cells[0][0].capacity * self.parallel_number  # Use the first cell's capacity

    def total_internal_resistance(self):
        """Calculate total internal resistance (series resistance increases)."""
        return self.cells[0][0].internal_resistance * self.series_number

    def out_current(self, input_current):
        """Output current is shared among parallel cells."""
        return input_current / self.parallel_number if self.parallel_number > 0 else input_current

    def total_soc(self):
        """Calculate average SOC across all series cells."""
        return sum(series[0].soc for series in self.cells) / self.series_number  # Only one cell per series needed

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
                if cell.soc > avg_soc + 1.0:  # If SOC is higher than average
                    cell.soc -= 0.1  # Simulate energy loss for balancing
