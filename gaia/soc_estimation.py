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


class _LinearOCV:
    """The original straight-line OCV model, kept as the default when no
    chemistry is given so existing code behaves as before."""

    def __init__(self, v_min: float = 3.0, v_max: float = 4.2):
        self.v_min, self.v_max = v_min, v_max

    def ocv(self, soc):
        return self.v_min + (self.v_max - self.v_min) * soc / 100.0

    def slope(self, soc):
        return (self.v_max - self.v_min) / 100.0


class KalmanFilterSOC:
    """
    Extended Kalman Filter (EKF) for SOC estimation on a 1-RC equivalent circuit.

    State x = [SOC (fraction), V_rc (V)].
        predict:  SOC -= I*dt / (3600*Q);   V_rc decays towards I*R1 with tau
        measure:  V = OCV(SOC) - I*R0 - V_rc
    With `chemistry` the OCV curve and its slope come from GAIA's PyBaMM-derived
    tables (gaia.ocv); without it a linear 3.0-4.2 V curve is used.
    """

    def __init__(self, nominal_capacity: float = 50.0, initial_soc: float = 100.0,
                 initial_covariance: float = 0.01, process_noise: float = 1e-7,
                 measurement_noise: float = 2.5e-5, chemistry: Optional[str] = None,
                 r0: Optional[float] = None, r1: Optional[float] = None, tau: float = 30.0):
        self.nominal_capacity = nominal_capacity  # Ah
        if chemistry:
            from .ocv import ocv_curve
            self.curve = ocv_curve(chemistry)
        else:
            self.curve = _LinearOCV()
        self.r0 = r0 if r0 is not None else 0.06 / nominal_capacity
        self.r1 = r1 if r1 is not None else 0.03 / nominal_capacity
        self.tau = tau
        self.x = np.array([initial_soc / 100.0, 0.0])
        self.P = np.diag([initial_covariance, 1e-4])
        self.Q = np.diag([process_noise, 1e-6])
        self.R = measurement_noise          # V^2
        self.last_innovation = 0.0

    # kept for backward compatibility
    @property
    def state(self):
        return np.array([[self.x[0]]])

    def ocv_from_soc(self, soc: float) -> float:
        return float(self.curve.ocv(soc * 100.0))

    def _adapt(self, innovation: float, s: float) -> None:
        """Hook for the adaptive variant."""

    def update(self, current: float, voltage: float, dt: float) -> float:
        """One step. current in A (positive = discharge), voltage in V. Returns SOC in %."""
        decay = np.exp(-dt / self.tau)
        # predict
        self.x[0] = np.clip(self.x[0] - current * dt / 3600.0 / self.nominal_capacity, 0.0, 1.0)
        self.x[1] = self.x[1] * decay + current * self.r1 * (1 - decay)
        F = np.diag([1.0, decay])
        self.P = F @ self.P @ F.T + self.Q
        # measure
        soc_pct = self.x[0] * 100.0
        predicted = float(self.curve.ocv(soc_pct)) - current * self.r0 - self.x[1]
        H = np.array([float(self.curve.slope(soc_pct)) * 100.0, -1.0])
        innovation = voltage - predicted
        s = float(H @ self.P @ H) + self.R
        K = self.P @ H / s
        self.x = self.x + K * innovation
        self.x[0] = np.clip(self.x[0], 0.0, 1.0)
        self.P = (np.eye(2) - np.outer(K, H)) @ self.P
        self.last_innovation = innovation
        self._adapt(innovation, s)
        return self.x[0] * 100.0

    def get_soc(self) -> float:
        return self.x[0] * 100.0


class AdaptiveExtendedKalmanFilterSOC(KalmanFilterSOC):
    """
    Adaptive EKF: same model as KalmanFilterSOC, but the measurement noise R is
    re-estimated from a sliding window of innovations, so the filter trusts
    the voltage less when the model and the cell disagree (high current,
    temperature, ageing) and more when they agree.
    """

    def __init__(self, nominal_capacity: float = 50.0, initial_soc: float = 100.0,
                 initial_covariance: float = 0.01, adaptive_factor: float = 0.95,
                 window_size: int = 20, **kwargs):
        super().__init__(nominal_capacity, initial_soc, initial_covariance, **kwargs)
        self.adaptive_factor = adaptive_factor
        self.window_size = window_size
        self.innovation_window: list = []

    def _adapt(self, innovation: float, s: float) -> None:
        self.innovation_window.append(innovation)
        if len(self.innovation_window) > self.window_size:
            self.innovation_window.pop(0)
        if len(self.innovation_window) >= 5:
            observed = float(np.mean(np.square(self.innovation_window)))
            self.R = float(np.clip(self.adaptive_factor * self.R + (1 - self.adaptive_factor) * observed,
                                   1e-6, 1e-2))


class SOCEstimator:
    """
    Unified SOC estimation interface supporting multiple algorithms.
    """
    
    def __init__(self, method: SOCEstimationMethod = SOCEstimationMethod.AEKF,
                 nominal_capacity: float = 50.0, initial_soc: float = 100.0, **model):
        """
        Initialize SOC estimator with specified method.
        
        Args:
            method: SOC estimation method to use
            nominal_capacity: Nominal battery capacity in Ah
            initial_soc: Initial SOC in percentage
        """
        self.method = method
        self.nominal_capacity = nominal_capacity
        self.model = model          # chemistry, r0, r1, tau for the Kalman filters
        
        if method == SOCEstimationMethod.COULOMB_COUNTING:
            self.estimator = CoulombCountingSOC(nominal_capacity, initial_soc)
        elif method == SOCEstimationMethod.KALMAN_FILTER:
            self.estimator = KalmanFilterSOC(nominal_capacity, initial_soc, **model)
        elif method == SOCEstimationMethod.AEKF:
            self.estimator = AdaptiveExtendedKalmanFilterSOC(nominal_capacity, initial_soc, **model)
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
                self.estimator = KalmanFilterSOC(self.nominal_capacity, initial_soc, **self.model)
            elif self.method == SOCEstimationMethod.AEKF:
                self.estimator = AdaptiveExtendedKalmanFilterSOC(self.nominal_capacity, initial_soc, **self.model)

