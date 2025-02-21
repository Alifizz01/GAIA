import json
import os

battery_spec_path = os.path.join(os.path.dirname(__file__), "..", "data", "battery_specs.json")

# ✅ Fix: Ensure load_battery_data() returns a dictionary
def load_battery_data():
    """Load battery chemistry specifications from JSON."""
    with open(battery_spec_path, "r") as file:
        return json.load(file)  # ✅ Returns dictionary

# ✅ Fix: Ensure chemistry retrieval is correct
def get_battery_chemistry(chemistry=None):
    """Retrieve battery chemistry from JSON, using default if not specified."""
    battery_chemistries = load_battery_data()

    if chemistry is None:
        chemistry = battery_chemistries["default"]  # ✅ Get the default chemistry name

    if chemistry in battery_chemistries:
        return battery_chemistries[chemistry]  # ✅ Correctly return the chemistry data
    else:
        raise ValueError(f"Battery chemistry '{chemistry}' not found.")

# ✅ Fix: Properly initialize Cell class with chemistry-specific data
class Cell:
    def __init__(
        self,
        soc: float = 100.0,
        chemistry=None,
        thermal_mass: float = 100.0,  # ✅ Can be modified based on chemistry
        c_rate=1
    ):
        self.chemistry_type = chemistry
        cell_data = get_battery_chemistry(self.chemistry_type)

        # ✅ Fix: Correct attributes
        self.nominal_capacity = cell_data["nominal_capacity"]
        self.nominal_voltage = cell_data["nominal_voltage"]  # ✅ Fix incorrect duplication
        self.internal_resistance = cell_data["internal_resistance"]
        self.discharge_efficiency = cell_data["discharge_efficiency"]
        self.charge_efficiency = cell_data["charge_efficiency"]
        self.energy_efficiency = cell_data.get("energy_efficiency", None)  # ✅ Handle missing field safely
        self.ocv_lookup = cell_data["ocv_lookup"]  # ✅ Add OCV lookup table

        if not 0 <= soc <= 100:
            raise ValueError("SOC must be between 0% and 100%!")

        self.soc = soc
        self.temperature = 25.0
        self.thermal_mass = thermal_mass
        self.c_rate = c_rate

# ✅ Fix: Correct `test_log()` function
def test_battery_cell_log():
    battery = Cell(chemistry="NMC")  # ✅ Chemistry must be a string
    print(f"Battery Chemistry: {battery.chemistry_type}")
    print(f"Nominal Voltage: {battery.nominal_voltage}V")
    print(f"Nominal Capacity: {battery.nominal_capacity}Ah")
    print(f"Internal Resistance: {battery.internal_resistance} mΩ")
    print(f"Charge Efficiency: {battery.charge_efficiency * 100}%")
    print(f"Discharge Efficiency: {battery.discharge_efficiency * 100}%")
    print(f"Max C-Rate: {battery.c_rate}C")

