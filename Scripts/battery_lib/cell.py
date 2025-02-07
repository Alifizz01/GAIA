from scipy.interpolate import interp1d

class Cell:
    # Class-level lookup table (shared across all cells)
    lookup_table = {
        "NMC": {0: 2.50, 10: 3.00, 20: 3.30, 30: 3.50, 40: 3.65, 50: 3.75, 60: 3.85, 70: 3.95, 80: 4.05, 90: 4.15, 100: 4.20},
        "NCA": {0: 2.70, 10: 3.20, 20: 3.40, 30: 3.55, 40: 3.70, 50: 3.80, 60: 3.90, 70: 4.00, 80: 4.10, 90: 4.15, 100: 4.20},
        "LFP": {0: 2.00, 10: 2.50, 20: 2.80, 30: 3.00, 40: 3.10, 50: 3.20, 60: 3.25, 70: 3.30, 80: 3.35, 90: 3.40, 100: 3.45},
        "LMO": {0: 2.50, 10: 3.00, 20: 3.30, 30: 3.50, 40: 3.65, 50: 3.75, 60: 3.85, 70: 3.95, 80: 4.05, 90: 4.15, 100: 4.20},
        "LTO": {0: 1.80, 10: 2.00, 20: 2.20, 30: 2.30, 40: 2.40, 50: 2.50, 60: 2.55, 70: 2.60, 80: 2.70, 90: 2.75, 100: 2.80}
    }

    def __init__(
        self,
        capacity: float,
        nominal_voltage: float,
        internal_resistance: float,
        cell_type: str = "NMC",      # Added cell_type to choose chemistry
        soc: float = 100.0,
        discharge_efficiency: float = 0.98,
        charge_efficiency: float = 0.95,
        thermal_mass: float = 100.0,
    ):
        if not 0 <= soc <= 100:
            raise ValueError("SOC must be between 0% and 100%!")

        self.capacity = capacity
        self.nominal_voltage = nominal_voltage  # Fixed missing =
        self.internal_resistance = internal_resistance  # Corrected name
        self.cell_type = cell_type
        self.soc = soc
        self.discharge_efficiency = discharge_efficiency
        self.charge_efficiency = charge_efficiency
        self.temperature = 25.0
        self.thermal_mass = thermal_mass
        self.voltage = nominal_voltage  # Initial voltage

    def update_soc(self, current: float, dt: float):
        """
        Update SOC using Coulomb counting with efficiency.
        - current: Positive for discharge, negative for charge (A)
        - dt: Time delta in seconds
        """
        if current == 0:
            return

        # Determine efficiency based on charge/discharge
        if current > 0:
            efficiency = self.discharge_efficiency
        else:
            efficiency = self.charge_efficiency

        delta_ah = (abs(current) * dt) / 3600  # Ah = A * h
        delta_soc = (delta_ah / self.capacity) * 100  # SOC change in %

        # Update SOC (add for charge, subtract for discharge)
        if current > 0:
            self.soc -= delta_soc * efficiency
        else:
            self.soc += delta_soc * efficiency

        # Clamp SOC between 0% and 100%
        self.soc = max(0.0, min(100.0, self.soc))

        # Update voltage based on new SOC
        self.update_voltage(current)

    def update_voltage(self, current: float):
        """Update terminal voltage using OCV curve and IR drop."""
        # Get OCV from lookup table
        soc_keys = list(self.lookup_table[self.cell_type].keys())
        closest_soc = min(soc_keys, key=lambda x: abs(x - self.soc))
        ocv = self.lookup_table[self.cell_type][closest_soc]  # Fixed typo

        # Calculate terminal voltage (V = OCV - I*R)
        self.voltage = ocv - (current * self.internal_resistance)

    def update_temperature(self, ambient_temp: float, dt: float):
        """
        Simulate temperature change due to power loss and ambient cooling.
        - ambient_temp: Ambient temperature (°C)
        - dt: Time delta in seconds
        """
        # Heat generated (I²R loss)
        power_loss = (self.current ** 2) * self.internal_resistance  # Watts
        
        # Heat dissipated to ambient (Newton's cooling)
        cooling_rate = 0.1  # W/°C (adjust based on cell design)
        heat_loss = cooling_rate * (self.temperature - ambient_temp)
        
        # Temperature change (ΔT = (Power - HeatLoss) * dt / ThermalMass)
        delta_temp = (power_loss - heat_loss) * dt / self.thermal_mass
        self.temperature += delta_temp

    def data_collection(self):
        """Log cell parameters (extend for database/CSV output)."""
        return {
            "soc": self.soc,
            "voltage": self.voltage,
            "temperature": self.temperature,
        }

    def data_prediction(self):
        """Placeholder for SOC prediction (e.g., Kalman filter)."""
        pass  # Implement later

    def data_correction(self):
        """Placeholder for SOC correction (e.g., voltage-based reset)."""
        pass  # Implement later