import numpy as np

class ThermalModel:
    def __init__(self, current=5, internal_resistance=0.01, initial_temperature=25, mass=0.2, heat_capacity=900, surface_area=0.02, heat_transfer_coefficient=10):
        self.internal_resistance = internal_resistance
        self.current = current
        self.mass = mass
        self.temperature = initial_temperature
        self.surface_area = surface_area
        self.heat_capacity = heat_capacity
        self.heat_transfer_coefficient = heat_transfer_coefficient

    def update_temperature(self, ambient_tempeature, dt):
        power_loss = (self.current ** 2) * self.internal_resistance
        heat_loss = self.heat_transfer_coefficient * self.surface_area * (self.temperature - ambient_tempeature)

        net_heat = power_loss - heat_loss
        delta_temp = (net_heat * dt)/ (self.mass * self.heat_capacity)
        self.temperature += delta_temp
        
        return self.temperature