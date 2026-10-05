"""Regenerate the README figures from real GAIA simulations.

    python assets/make_figures.py        # needs pybamm + matplotlib, Python 3.9-3.12
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from gaia import BatteryModel  # noqa: E402

INK, MUTED, GRID = "#1F2933", "#65707D", "#E3E7EC"
COLORS = {"NMC": "#2F6FDE", "LFP": "#1E9E6A", "NCA": "#D9822B"}
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})


def discharge(chem, c_rate=1.0, model="SPM"):
    bm = BatteryModel(model, chem)
    cap = bm.parameter_values["Nominal cell capacity [A.h]"]
    bm.change_parameters("Current function [A]", cap * c_rate)
    sol = bm.run_simulation(duration=int(3600 / c_rate * 1.05))
    q = sol["Discharge capacity [A.h]"].entries
    v = sol["Voltage [V]"].entries
    return 100 * (1 - q / cap), v, cap


fig, ax = plt.subplots(figsize=(7.2, 3.6))
for chem in ("NMC", "LFP", "NCA"):
    soc, v, cap = discharge(chem)
    ax.plot(soc, v, lw=2.2, color=COLORS[chem], label=f"{chem}  ({cap:.2f} Ah cell)")
ax.set_xlim(100, 0)
ax.set_xlabel("State of charge [%]")
ax.set_ylabel("Terminal voltage [V]")
ax.set_title("1C discharge, PyBaMM single particle model", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "discharge_chemistries.png"))

fig, ax = plt.subplots(figsize=(7.2, 3.6))
for rate, shade in ((0.5, "#8DB3F2"), (1.0, "#2F6FDE"), (2.0, "#14398A")):
    soc, v, _ = discharge("NMC", rate, "SPMe")
    ax.plot(100 - soc, v, lw=2.2, color=shade, label=f"{rate:g}C")
ax.set_xlim(0, 100)
ax.set_xlabel("Capacity delivered [% of nominal]")
ax.set_ylabel("Terminal voltage [V]")
ax.set_title("NMC rate capability: more current, more polarisation, lower voltage (SPMe)", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, title="C-rate")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "rate_capability.png"))
# --- SOC estimator accuracy against PyBaMM truth
from gaia.soc_benchmark import run_benchmark  # noqa: E402

r = run_benchmark("NMC")
fig, ax = plt.subplots(figsize=(7.2, 3.6))
tm = r["t"] / 60
ax.plot(tm, r["soc_true"], color=INK, lw=2.6, label="true SOC (PyBaMM SPMe)")
names = {"COULOMB_COUNTING": ("Coulomb counting", "#B8642A"), "KALMAN_FILTER": ("EKF", "#2F6FDE"),
         "AEKF": ("Adaptive EKF", "#0E7C66")}
for key, (label, color) in names.items():
    ax.plot(tm, r["estimates"][key], color=color, lw=1.6,
            label=f"{label}: {r['rmse_after_10min'][key]:.1f} % RMSE")
ax.set_xlabel("Time [min]")
ax.set_ylabel("State of charge [%]")
ax.set_title("SOC estimators vs electrochemical truth: 20 % wrong start, noisy, biased sensors",
             loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "soc_accuracy.png"))
print("figures written to", HERE)
