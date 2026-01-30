# GAIA Installation Guide

## Python Version Requirements

**IMPORTANT**: GAIA requires **Python 3.9, 3.10, 3.11, or 3.12**.

PyBaMM (the underlying battery modeling library) does not yet support Python 3.13+. If you're using Python 3.13 or later, please use Python 3.12 instead.

### Checking Your Python Version

```bash
python --version
```

If you have Python 3.13+, you'll need to:

1. **Install Python 3.12** alongside your current version
2. **Use Python 3.12** for this project:
   ```bash
   python3.12 -m pip install -e .
   ```

Or create a virtual environment with Python 3.12:

```bash
# Using pyenv (recommended)
pyenv install 3.12.0
pyenv local 3.12.0

# Using venv
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/GAIA.git
cd GAIA
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Using Python 3.9-3.12
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install GAIA (Editable Mode)

```bash
pip install -e .
```

This installs GAIA in editable mode, so changes to the source code are immediately reflected.

## Alternative Installation Methods

### Using Conda

If you prefer conda:

```bash
# Create conda environment with Python 3.12
conda create -n gaia python=3.12
conda activate gaia

# Install PyBaMM from conda-forge
conda install -c conda-forge pybamm

# Install other dependencies
pip install -r requirements.txt

# Install GAIA
pip install -e .
```

### Manual Installation (Without pip install -e)

If you encounter issues with `pip install -e .`, you can run GAIA directly:

```bash
# Install dependencies only
pip install -r requirements.txt

# Run directly from Scripts directory
cd Scripts
python gui/main_window.py
```

## Troubleshooting

### Issue: "No matching distribution found for pybamm"

**Solution**: This means your Python version is not compatible. PyBaMM requires Python 3.9-3.12.

1. Check your Python version: `python --version`
2. If you have Python 3.13+, install Python 3.12
3. Use Python 3.12 for this project

### Issue: PyQt5 Installation Fails

**Solution**: PyQt5 can be tricky on some systems. Try:

```bash
# On Windows/Linux
pip install PyQt5

# On macOS, you might need:
pip install PyQt5 --upgrade

# Or use conda
conda install -c conda-forge pyqt
```

### Issue: PyBaMM Import Errors

**Solution**: Ensure PyBaMM is properly installed:

```bash
pip uninstall pybamm
pip install pybamm
python -c "import pybamm; print(pybamm.__version__)"
```

### Issue: Permission Errors on Windows

**Solution**: Use the `--user` flag:

```bash
pip install --user -r requirements.txt
pip install --user -e .
```

## Verifying Installation

After installation, verify everything works:

```python
# Test imports
python -c "from bms_core import BatteryModel; print('✓ Core modules OK')"
python -c "from gui import main_window; print('✓ GUI modules OK')"
```

## Development Installation

For development, install with dev dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- pytest-cov (coverage)
- black (code formatting)
- flake8 (linting)

## Next Steps

After successful installation:

1. Read the [Quick Start Guide](QUICKSTART.md)
2. Check the [README.md](README.md) for full documentation
3. Try running the GUI: `python Scripts/gui/main_window.py`

## Support

If you encounter installation issues:

1. Check that you're using Python 3.9-3.12
2. Ensure all dependencies are installed
3. Create an issue on GitHub with:
   - Your Python version (`python --version`)
   - Error messages
   - Operating system information

