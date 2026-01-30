"""
State of Charge (SOC) Estimation Module for GAIA BMS Framework
Implements multiple SOC estimation algorithms including Coulomb Counting, 
Kalman Filter, and Adaptive Extended Kalman Filter (AEKF).
"""

import numpy as np
from typing import Optional, Tuple
from enum import Enum


class SOCEstimationMethod(Enum):
    """Available SOC estimation methods."""
    COULOMB_COUNTING = "coulomb_counting"
    KALMAN_FILTER = "kalman_filter"
    AEKF = "aekf"  # Adaptive Extended Kalman Filter


class CoulombCountingSOC:
    """
    Simple Coulomb Counting method for SOC estimation.
    Integrates current over time to estimate SOC.
    """
    
    def __init__(self, nominal_capacity: float = 50.0, initial_soc: float = 100.0,
                 coulombic_efficiency: float = 0.98):
        """
        Initialize Coulomb Counting estimator.
        
        Args:
            nominal_capacity: Nominal battery capacity in Ah
            initial_soc: Initial SOC in percentage (0-100)
            coulombic_efficiency: Coulombic efficiency (charge/discharge)
        """
        self.nominal_capacity = nominal_capacity  # Ah
        self.current_soc = initial_soc / 100.0  # Convert to fraction
        self.coulombic_efficiency = coulombic_efficiency
        self.total_charge = (initial_soc / 100.0) * nominal_capacity  # Ah
        
    def update(self, current: float, dt: float) -> float:
        """
        Update SOC based on current and time step.
        
        Args:
            current: Current in Amperes (positive for discharge, negative for charge)
            dt: Time step in seconds
            
        Returns:
            Updated SOC as percentage (0-100)
        """
        # Convert dt from seconds to hours
        dt_hours = dt / 3600.0
        
        # Calculate charge change (negative current = charging)
        if current < 0:  # Charging
            charge_change = abs(current) * dt_hours * self.coulombic_efficiency
        else:  # Discharging
            charge_change = -current * dt_hours / self.coulombic_efficiency
        
        # Update total charge
        self.total_charge += charge_change
        
        # Calculate SOC
        self.current_soc = np.clip(self.total_charge / self.nominal_capacity, 0.0, 1.0)
        
        return self.current_soc * 100.0  # Return as percentage
    
    def reset(self, initial_soc: float = 100.0):
        """Reset the estimator to a new initial SOC."""
        self.current_soc = initial_soc / 100.0
        self.total_charge = self.current_soc * self.nominal_capacity
    
    def get_soc(self) -> float:
        """Get current SOC estimate."""
        return self.current_soc * 100.0


class KalmanFilterSOC:
    """
    Extended Kalman Filter (EKF) for SOC estimation.
    Provides better accuracy than Coulomb Counting by incorporating voltage measurements.
    """
    
    def __init__(self, nominal_capacity: float = 50.0, initial_soc: float = 100.0,
                 initial_covariance: float = 0.01, process_noise: float = 0.001,
                 measurement_noise: float = 0.01):
        """
        Initialize Kalman Filter for SOC estimation.
        
        Args:
            nominal_capacity: Nominal battery capacity in Ah
            initial_soc: Initial SOC in percentage (0-100)
            initial_covariance: Initial state covariance
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
        """
        self.nominal_capacity = nominal_capacity  # Ah
        self.state = np.array([[initial_soc / 100.0]])  # SOC as fraction
        self.P = np.array([[initial_covariance]])  # State covariance
        
        # Noise covariances
        self.Q = np.array([[process_noise]])  # Process noise
        self.R = np.array([[measurement_noise]])  # Measurement noise
        
        # OCV-SOC curve parameters (simplified linear model)
        self.ocv_max = 4.2  # V at 100% SOC
        self.ocv_min = 3.0  # V at 0% SOC
        
    def ocv_from_soc(self, soc: float) -> float:
        """Convert SOC to OCV using linear model."""
        return self.ocv_min + (self.ocv_max - self.ocv_min) * soc
    
    def soc_from_ocv(self, ocv: float) -> float:
        """Convert OCV to SOC using linear model."""
        return np.clip((ocv - self.ocv_min) / (self.ocv_max - self.ocv_min), 0.0, 1.0)
    
    def update(self, current: float, voltage: float, dt: float) -> float:
        """
        Update SOC estimate using Kalman Filter.
        
        Args:
            current: Current in Amperes
            voltage: Terminal voltage in Volts
            dt: Time step in seconds
            
        Returns:
            Updated SOC as percentage (0-100)
        """
        dt_hours = dt / 3600.0
        
        # State transition (Coulomb Counting)
        soc_change = -current * dt_hours / self.nominal_capacity
        self.state[0, 0] += soc_change
        self.state[0, 0] = np.clip(self.state[0, 0], 0.0, 1.0)
        
        # Predict covariance
        self.P = self.P + self.Q
        
        # Measurement model: voltage = OCV(SOC) - I*R
        # Simplified: use OCV directly (assuming small current or known R)
        predicted_ocv = self.ocv_from_soc(self.state[0, 0])
        measurement = voltage
        innovation = measurement - predicted_ocv
        
        # Measurement Jacobian (derivative of OCV w.r.t. SOC)
        H = np.array([[(self.ocv_max - self.ocv_min)]])
        
        # Kalman gain
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K * innovation
        self.state[0, 0] = np.clip(self.state[0, 0], 0.0, 1.0)
        
        # Update covariance
        self.P = (np.eye(1) - K @ H) @ self.P
        
        return self.state[0, 0] * 100.0
    
    def get_soc(self) -> float:
        """Get current SOC estimate."""
        return self.state[0, 0] * 100.0


class AdaptiveExtendedKalmanFilterSOC:
    """
    Adaptive Extended Kalman Filter (AEKF) for SOC estimation.
    Adapts noise covariances based on innovation sequence for better accuracy.
    """
    
    def __init__(self, nominal_capacity: float = 50.0, initial_soc: float = 100.0,
                 initial_covariance: float = 0.01, adaptive_factor: float = 0.95):
        """
        Initialize Adaptive Extended Kalman Filter.
        
        Args:
            nominal_capacity: Nominal battery capacity in Ah
            initial_soc: Initial SOC in percentage (0-100)
            initial_covariance: Initial state covariance
            adaptive_factor: Forgetting factor for adaptive noise estimation
        """
        self.nominal_capacity = nominal_capacity
        self.state = np.array([[initial_soc / 100.0]])
        self.P = np.array([[initial_covariance]])
        
        # Adaptive noise parameters
        self.adaptive_factor = adaptive_factor
        self.R = np.array([[0.01]])  # Initial measurement noise
        self.Q = np.array([[0.001]])  # Initial process noise
        
        # Innovation sequence for adaptation
        self.innovation_window = []
        self.window_size = 10
        
        # OCV-SOC parameters
        self.ocv_max = 4.2
        self.ocv_min = 3.0
        
    def ocv_from_soc(self, soc: float) -> float:
        """Convert SOC to OCV."""
        return self.ocv_min + (self.ocv_max - self.ocv_min) * soc
    
    def update(self, current: float, voltage: float, dt: float) -> float:
        """
        Update SOC using Adaptive Extended Kalman Filter.
        
        Args:
            current: Current in Amperes
            voltage: Terminal voltage in Volts
            dt: Time step in seconds
            
        Returns:
            Updated SOC as percentage (0-100)
        """
        dt_hours = dt / 3600.0
        
        # Predict step (Coulomb Counting)
        soc_change = -current * dt_hours / self.nominal_capacity
        self.state[0, 0] += soc_change
        self.state[0, 0] = np.clip(self.state[0, 0], 0.0, 1.0)
        
        # Predict covariance
        self.P = self.P + self.Q
        
        # Measurement step
        predicted_ocv = self.ocv_from_soc(self.state[0, 0])
        innovation = voltage - predicted_ocv
        
        # Store innovation for adaptation
        self.innovation_window.append(innovation)
        if len(self.innovation_window) > self.window_size:
            self.innovation_window.pop(0)
        
        # Adaptive measurement noise estimation
        if len(self.innovation_window) >= 5:
            innovation_variance = np.var(self.innovation_window)
            # Adaptive update with forgetting factor
            self.R[0, 0] = (self.adaptive_factor * self.R[0, 0] + 
                           (1 - self.adaptive_factor) * innovation_variance)
            self.R[0, 0] = np.clip(self.R[0, 0], 0.001, 0.1)
        
        # Measurement Jacobian
        H = np.array([[(self.ocv_max - self.ocv_min)]])
        
        # Kalman gain
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K * innovation
        self.state[0, 0] = np.clip(self.state[0, 0], 0.0, 1.0)
        
        # Update covariance
        self.P = (np.eye(1) - K @ H) @ self.P
        
        return self.state[0, 0] * 100.0
    
    def get_soc(self) -> float:
        """Get current SOC estimate."""
        return self.state[0, 0] * 100.0


class SOCEstimator:
    """
    Unified SOC estimation interface supporting multiple algorithms.
    """
    
    def __init__(self, method: SOCEstimationMethod = SOCEstimationMethod.AEKF,
                 nominal_capacity: float = 50.0, initial_soc: float = 100.0):
        """
        Initialize SOC estimator with specified method.
        
        Args:
            method: SOC estimation method to use
            nominal_capacity: Nominal battery capacity in Ah
            initial_soc: Initial SOC in percentage
        """
        self.method = method
        self.nominal_capacity = nominal_capacity
        
        if method == SOCEstimationMethod.COULOMB_COUNTING:
            self.estimator = CoulombCountingSOC(nominal_capacity, initial_soc)
        elif method == SOCEstimationMethod.KALMAN_FILTER:
            self.estimator = KalmanFilterSOC(nominal_capacity, initial_soc)
        elif method == SOCEstimationMethod.AEKF:
            self.estimator = AdaptiveExtendedKalmanFilterSOC(nominal_capacity, initial_soc)
        else:
            raise ValueError(f"Unknown SOC estimation method: {method}")
    
    def update(self, current: float, voltage: Optional[float] = None, dt: float = 1.0) -> float:
        """
        Update SOC estimate.
        
        Args:
            current: Current in Amperes
            voltage: Terminal voltage in Volts (required for KF/AEKF)
            dt: Time step in seconds
            
        Returns:
            Updated SOC as percentage (0-100)
        """
        if self.method == SOCEstimationMethod.COULOMB_COUNTING:
            return self.estimator.update(current, dt)
        else:
            if voltage is None:
                raise ValueError("Voltage measurement required for Kalman Filter methods")
            return self.estimator.update(current, voltage, dt)
    
    def get_soc(self) -> float:
        """Get current SOC estimate."""
        return self.estimator.get_soc()
    
    def reset(self, initial_soc: float = 100.0):
        """Reset the estimator."""
        if hasattr(self.estimator, 'reset'):
            self.estimator.reset(initial_soc)
        else:
            # Reinitialize for methods without reset
            if self.method == SOCEstimationMethod.COULOMB_COUNTING:
                self.estimator = CoulombCountingSOC(self.nominal_capacity, initial_soc)
            elif self.method == SOCEstimationMethod.KALMAN_FILTER:
                self.estimator = KalmanFilterSOC(self.nominal_capacity, initial_soc)
            elif self.method == SOCEstimationMethod.AEKF:
                self.estimator = AdaptiveExtendedKalmanFilterSOC(self.nominal_capacity, initial_soc)

