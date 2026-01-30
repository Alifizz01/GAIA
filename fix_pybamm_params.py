<<<<<<< HEAD
"""
Script to fix PyBaMM parameter set issues.
Attempts to download and install missing parameter sets.
"""

import sys
import subprocess
import os

def check_pybamm():
    """Check PyBaMM installation."""
    try:
        import pybamm
        print(f"[OK] PyBaMM is installed (version: {pybamm.__version__})")
        return True
    except ImportError:
        print("[X] PyBaMM is not installed")
        return False

def check_parameter_sets():
    """Check available parameter sets."""
    try:
        import pybamm
        print("\nChecking parameter sets...")
        
        test_sets = ["Ai2020", "Marquis2019", "Prada2013", "Chen2020"]
        available = []
        
        for name in test_sets:
            try:
                pybamm.ParameterValues(name)
                print(f"  [OK] {name}")
                available.append(name)
            except:
                print(f"  [X] {name}")
        
        return available
    except Exception as e:
        print(f"Error checking parameter sets: {e}")
        return []

def reinstall_pybamm():
    """Reinstall PyBaMM."""
    print("\nAttempting to reinstall PyBaMM...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pybamm"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "pybamm"], check=True)
        print("[OK] PyBaMM reinstalled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to reinstall PyBaMM: {e}")
        return False

def install_with_extras():
    """Install PyBaMM with all extras."""
    print("\nInstalling PyBaMM with all extras...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pybamm[all]"], check=True)
        print("[OK] PyBaMM with extras installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to install extras: {e}")
        return False

def try_download_params():
    """Try to trigger parameter set download."""
    print("\nAttempting to download parameter sets...")
    try:
        import pybamm
        # Try to create a parameter set - this might trigger download
        print("  Trying to load parameter set (this may download files)...")
        params = pybamm.ParameterValues("Ai2020")
        print("  [OK] Parameter set loaded/downloaded")
        return True
    except Exception as e:
        print(f"  [X] Could not download: {e}")
        return False

def main():
    print("="*70)
    print("PyBaMM Parameter Set Fixer")
    print("="*70)
    
    # Check Python version
    python_version = sys.version_info
    print(f"\nPython version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major == 3 and python_version.minor >= 13:
        print("WARNING: Python 3.13+ may not be fully supported by PyBaMM")
        print("   Consider using Python 3.9-3.12 for best compatibility")
    
    # Check PyBaMM
    if not check_pybamm():
        print("\nInstalling PyBaMM...")
        if not reinstall_pybamm():
            print("\n[X] Failed to install PyBaMM. Please install manually:")
            print("   pip install pybamm")
            return False
    
    # Check parameter sets
    available = check_parameter_sets()
    
    if not available:
        print("\n[!] No parameter sets found. Attempting fixes...")
        
        # Try reinstalling
        if reinstall_pybamm():
            available = check_parameter_sets()
        
        # Try installing with extras
        if not available:
            if install_with_extras():
                available = check_parameter_sets()
        
        # Try downloading
        if not available:
            try_download_params()
            available = check_parameter_sets()
    
    # Final status
    print("\n" + "="*70)
    if available:
        print(f"[OK] SUCCESS: Found {len(available)} parameter set(s)")
        print(f"  Available: {', '.join(available)}")
        print("\nYou should now be able to run GAIA successfully!")
        return True
    else:
        print("[X] FAILED: Still no parameter sets found")
        print("\nManual fixes:")
        print("1. Use Python 3.9-3.12 (recommended)")
        print("2. Try: pip install --upgrade pybamm")
        print("3. Try: pip install pybamm[all]")
        print("4. Check PyBaMM documentation for parameter set installation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

=======
"""
Script to fix PyBaMM parameter set issues.
Attempts to download and install missing parameter sets.
"""

import sys
import subprocess
import os

def check_pybamm():
    """Check PyBaMM installation."""
    try:
        import pybamm
        print(f"[OK] PyBaMM is installed (version: {pybamm.__version__})")
        return True
    except ImportError:
        print("[X] PyBaMM is not installed")
        return False

def check_parameter_sets():
    """Check available parameter sets."""
    try:
        import pybamm
        print("\nChecking parameter sets...")
        
        test_sets = ["Ai2020", "Marquis2019", "Prada2013", "Chen2020"]
        available = []
        
        for name in test_sets:
            try:
                pybamm.ParameterValues(name)
                print(f"  [OK] {name}")
                available.append(name)
            except:
                print(f"  [X] {name}")
        
        return available
    except Exception as e:
        print(f"Error checking parameter sets: {e}")
        return []

def reinstall_pybamm():
    """Reinstall PyBaMM."""
    print("\nAttempting to reinstall PyBaMM...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pybamm"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "pybamm"], check=True)
        print("[OK] PyBaMM reinstalled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to reinstall PyBaMM: {e}")
        return False

def install_with_extras():
    """Install PyBaMM with all extras."""
    print("\nInstalling PyBaMM with all extras...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pybamm[all]"], check=True)
        print("[OK] PyBaMM with extras installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to install extras: {e}")
        return False

def try_download_params():
    """Try to trigger parameter set download."""
    print("\nAttempting to download parameter sets...")
    try:
        import pybamm
        # Try to create a parameter set - this might trigger download
        print("  Trying to load parameter set (this may download files)...")
        params = pybamm.ParameterValues("Ai2020")
        print("  [OK] Parameter set loaded/downloaded")
        return True
    except Exception as e:
        print(f"  [X] Could not download: {e}")
        return False

def main():
    print("="*70)
    print("PyBaMM Parameter Set Fixer")
    print("="*70)
    
    # Check Python version
    python_version = sys.version_info
    print(f"\nPython version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major == 3 and python_version.minor >= 13:
        print("WARNING: Python 3.13+ may not be fully supported by PyBaMM")
        print("   Consider using Python 3.9-3.12 for best compatibility")
    
    # Check PyBaMM
    if not check_pybamm():
        print("\nInstalling PyBaMM...")
        if not reinstall_pybamm():
            print("\n[X] Failed to install PyBaMM. Please install manually:")
            print("   pip install pybamm")
            return False
    
    # Check parameter sets
    available = check_parameter_sets()
    
    if not available:
        print("\n[!] No parameter sets found. Attempting fixes...")
        
        # Try reinstalling
        if reinstall_pybamm():
            available = check_parameter_sets()
        
        # Try installing with extras
        if not available:
            if install_with_extras():
                available = check_parameter_sets()
        
        # Try downloading
        if not available:
            try_download_params()
            available = check_parameter_sets()
    
    # Final status
    print("\n" + "="*70)
    if available:
        print(f"[OK] SUCCESS: Found {len(available)} parameter set(s)")
        print(f"  Available: {', '.join(available)}")
        print("\nYou should now be able to run GAIA successfully!")
        return True
    else:
        print("[X] FAILED: Still no parameter sets found")
        print("\nManual fixes:")
        print("1. Use Python 3.9-3.12 (recommended)")
        print("2. Try: pip install --upgrade pybamm")
        print("3. Try: pip install pybamm[all]")
        print("4. Check PyBaMM documentation for parameter set installation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

>>>>>>> e25e88bc9d309c3e29a000420b6d5c43e3c84787
