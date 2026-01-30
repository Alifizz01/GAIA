# Installing PyBaMM Parameter Sets

If you're getting errors about missing PyBaMM parameter sets, follow these steps:

## Issue
PyBaMM parameter sets (like "Ai2020", "Marquis2019", etc.) are not always included by default and may need to be downloaded separately.

## Solutions

### Option 1: Reinstall PyBaMM (Recommended)
```bash
pip uninstall pybamm
pip install pybamm
```

### Option 2: Install with All Extras
```bash
pip install pybamm[all]
```

### Option 3: Use Compatible Python Version
PyBaMM works best with Python 3.9-3.12. Python 3.13+ may have compatibility issues.

```bash
# If using pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Then reinstall PyBaMM
pip install pybamm
```

### Option 4: Download Parameter Sets Manually
PyBaMM parameter sets are usually downloaded automatically on first use. If they're not downloading:

1. Check your internet connection
2. Check PyBaMM cache directory: `~/.pybamm/`
3. Try running: `python -c "import pybamm; pybamm.ParameterValues('Ai2020')"`

### Option 5: Check PyBaMM Installation
```bash
python -c "import pybamm; print(pybamm.__version__); print(pybamm.__file__)"
```

This will show your PyBaMM version and installation path.

## Verify Installation
Run the check script:
```bash
python check_pybamm_params.py
```

This will test which parameter sets are available.

## Common Parameter Sets
- **Ai2020**: Generic lithium-ion (good default)
- **Marquis2019**: LFP chemistry
- **Chen2020**: NMC chemistry
- **Prada2013**: Various chemistries

## Still Having Issues?
1. Ensure you're using Python 3.9-3.12
2. Try a fresh virtual environment
3. Check PyBaMM GitHub issues for parameter set problems
4. Consider using a conda environment instead

