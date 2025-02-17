import numpy as np

class SOCEstimator:
    def __init__(self, initial_soc=100.0, process_variance=1e-4, measurement_variance=0.01, initial_capacity=74):
        """Initialize the Kalman Filter for SOC estimation."""
        self.soc = initial_soc  # Initial SOC (%)
        self.process_variance = process_variance  # Variance in the SOC model
        self.measurement_variance = measurement_variance  # Variance in voltage measurements
        self.initial_capatity = initial_capacity

        # Kalman Filter variables
        self.estimate = initial_soc  # State estimate (SOC)
        self.error_covariance = 1.0  # Initial estimation uncertainty

    def update(self, measured_voltage, current, dt, ocv_lookup):
        delta_ah =  (current * dt)/3600
        predicted_soc = self.estimate - (delta_ah/self.initial_capatity) * 100

        soc_keys = list(ocv_lookup.keys())
        closest_soc = min(soc_keys, key=lambda x: abs(x - predicted_soc))
        estimated_voltage = ocv_lookup[closest_soc]

        kalman_gain = self.error_covariance / (self.error_covariance + self.measurement_variance)
        self.estimate = predicted_soc + kalman_gain * (measured_voltage - estimated_voltage)
        self.error_covariance = (1 - kalman_gain) * self.error_covariance + self.process_variance

        self.estimate = max(0, min (100, self.estimate))

        return self.estimate