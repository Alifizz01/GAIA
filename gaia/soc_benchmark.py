"""How good is each SOC estimator, measured against electrochemical truth?

The "true" cell is a PyBaMM model (SPMe by default) driven by a pulsed load.
Its current and voltage are then measured the way a BMS would see them:
with Gaussian noise and a constant current-sensor offset. Each estimator gets
those measurements and a deliberately wrong starting SOC. None of them shares
the truth model: the Kalman filters only know the chemistry's OCV table and a
guessed resistance, so the comparison is fair.

    from gaia.soc_benchmark import run_benchmark
    result = run_benchmark("NMC")          # dict with traces and RMSE per method
"""
from __future__ import annotations

import numpy as np

from .soc_estimation import SOCEstimationMethod, SOCEstimator


def load_profile(capacity: float, duration: float = 3600.0, dt: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """A drive-like pulsed load: 1C, 0.5C, 2C bursts and rests (A, positive = discharge)."""
    t = np.arange(0.0, duration, dt)
    pattern = [(120, 1.0), (60, 0.0), (90, 2.0), (60, 0.5), (45, 0.0), (75, 1.5)]
    period = sum(seconds for seconds, _ in pattern)
    current = np.empty_like(t)
    for k, tk in enumerate(t):
        x = tk % period
        for seconds, c_rate in pattern:
            if x < seconds:
                current[k] = c_rate * capacity
                break
            x -= seconds
    return t, current


def simulate_truth(chemistry: str, t: np.ndarray, current: np.ndarray, model: str = "SPMe") -> dict:
    """Drive the PyBaMM cell with `current` and return true SOC and voltage on `t`."""
    import pybamm

    from .battery_model import BatteryModel
    bm = BatteryModel(model, chemistry)
    capacity = bm.parameter_values["Nominal cell capacity [A.h]"]
    bm.change_parameters("Current function [A]", pybamm.Interpolant(t, current, pybamm.t))
    solution = bm.simulation.solve([0, float(t[-1])], t_interp=t)
    time = solution["Time [s]"].entries
    soc = 100.0 * (1.0 - solution["Discharge capacity [A.h]"].entries / capacity)
    voltage = solution["Voltage [V]"].entries
    return {"t": time, "soc": soc, "voltage": voltage, "current": np.interp(time, t, current),
            "capacity": capacity}


def run_benchmark(chemistry: str = "NMC", duration: float = 2700.0, initial_soc_guess: float = 80.0,
                  voltage_noise: float = 0.005, current_noise: float = 0.02, current_offset: float = 0.01,
                  seed: int = 0, model: str = "SPMe") -> dict:
    """Noise in V and fraction of capacity (current); offset as a fraction of capacity."""
    from .battery_model import BatteryModel
    capacity = BatteryModel(model, chemistry).parameter_values["Nominal cell capacity [A.h]"]
    t, current = load_profile(capacity, duration)
    truth = simulate_truth(chemistry, t, current, model)
    rng = np.random.default_rng(seed)
    n = len(truth["t"])
    meas_i = truth["current"] + rng.normal(0, current_noise * capacity, n) + current_offset * capacity
    meas_v = truth["voltage"] + rng.normal(0, voltage_noise, n)
    dt = np.diff(truth["t"], prepend=0.0)

    estimates = {}
    for method in SOCEstimationMethod:
        model_args = {} if method == SOCEstimationMethod.COULOMB_COUNTING else {"chemistry": chemistry}
        est = SOCEstimator(method=method, nominal_capacity=capacity, initial_soc=initial_soc_guess, **model_args)
        trace = [est.update(i, v, d) if method != SOCEstimationMethod.COULOMB_COUNTING else est.update(i, dt=d)
                 for i, v, d in zip(meas_i, meas_v, dt)]
        estimates[method.name] = np.asarray(trace)

    settled = truth["t"] >= 600.0          # judge accuracy after a 10 minute convergence window
    rmse = {name: float(np.sqrt(np.mean((trace[settled] - truth["soc"][settled]) ** 2)))
            for name, trace in estimates.items()}
    final_error = {name: float(abs(trace[-1] - truth["soc"][-1])) for name, trace in estimates.items()}
    return {"chemistry": chemistry, "capacity": capacity, "t": truth["t"], "soc_true": truth["soc"],
            "voltage": truth["voltage"], "current": truth["current"], "estimates": estimates,
            "rmse_after_10min": rmse, "final_error": final_error,
            "conditions": {"initial_soc_guess": initial_soc_guess, "voltage_noise_V": voltage_noise,
                           "current_noise_frac": current_noise, "current_offset_frac": current_offset}}
