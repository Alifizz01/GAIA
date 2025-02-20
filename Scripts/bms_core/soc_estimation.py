import numpy as np

class SOCEstimator:
    def __init__(self, initial_soc=100.0, process_variance=1e-4, measurement_variance=0.01, initial_capacity=74):
        """Initialize the Kalman Filter for SOC estimation."""
        self.soc = initial_soc  # Initial SOC (%)
        self.process_variance = process_variance  # Variance in the SOC model
        self.measurement_variance = measurement_variance  # Variance in voltage measurements

        # Kalman Filter variables
        self.estimate = initial_soc  # State estimate (SOC)
        self.error_covariance = 1.0  # Initial estimation uncertainty
        self.initial_capacity = initial_capacity  # Battery capacity in Ah

    def update(self, measured_voltage, current, dt, ocv_lookup):
        """Update SOC using the Kalman Filter approach."""
        
        # Step 1: Predict SOC using Coulomb counting
        delta_ah = (current * dt) / 3600  # Convert current from A*s to Ah
        predicted_soc = self.estimate - (delta_ah / self.initial_capacity) * 100  # Fix: Use initial_capacity

        # Step 2: Get OCV from lookup table
        soc_keys = list(ocv_lookup.keys())
        closest_soc = min(soc_keys, key=lambda x: abs(x - predicted_soc))
        estimated_voltage = ocv_lookup[closest_soc]

        # Step 3: Compute Kalman Gain
        kalman_gain = self.error_covariance / (self.error_covariance + self.measurement_variance)

        # Step 4: Correct SOC estimate using voltage difference
        self.estimate = predicted_soc + kalman_gain * (measured_voltage - estimated_voltage)

        # Step 5: Update error covariance
        self.error_covariance = (1 - kalman_gain) * self.error_covariance + self.process_variance

        # Clamp SOC between 0% and 100%
        self.estimate = max(0, min(100, self.estimate))

        return self.estimate
