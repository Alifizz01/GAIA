# GAIA in MATLAB and Simulink

Verified on MATLAB R2025a (Simulink) with Python 3.12.

GAIA's pack model and BMS run in Python; these files let MATLAB and Simulink drive
them through MATLAB's built-in Python interface. No server, no copies of the
physics: results are identical to GAIA Studio and the Python API.

## One-time setup

1. Use a Python that MATLAB supports and PyBaMM supports: **3.9 to 3.12**.
2. Install GAIA into it: `python -m pip install -e <path to this repository>`
3. In a fresh MATLAB session, before anything else:

```matlab
addpath('<repository>/matlab')
gaia_setup('C:\path\to\.venv\Scripts\python.exe')
```

## MATLAB

```matlab
pack = GaiaPack(12, "NMC", 50, 80);     % 12 cells in series, NMC, 50 Ah, 80 % SOC
pack.setCurrent(50);                    % A, positive = discharge
T = pack.runFor(1800);                  % table: time_s, pack_voltage_V, soc_estimated_pct, ...
pack.injectFault(3, "overheat");        % overheat | short | fade | heal
y = pack.step(1)                        % one step as a struct
pack.resetFault()                       % refused while the condition is still present
```

`gaia_matlab_example.m` runs a discharge, an over-temperature trip and the recovery, and plots it.

## Simulink

`GaiaBMS.m` is a `matlab.System` block: requested current in; pack voltage, actual
current, SOC estimate, true SOC, hottest cell temperature, BMS state and fault flag out.
It runs in *Interpreted execution* mode because the physics is Python.

```matlab
build_gaia_simulink_demo          % builds gaia_bms_demo.slx and runs a 45 min drive profile
```

Replace the *Load profile* source with your own charger or traction controller to
close the loop around GAIA's BMS.
