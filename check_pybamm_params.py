<<<<<<< HEAD
"""Quick script to check PyBaMM parameter set availability"""
import pybamm

print(f"PyBaMM version: {pybamm.__version__}")
print("\nTesting parameter sets...")

test_sets = [
    "Ai2020", "Marquis2019", "Prada2013", "Chen2020",
    "Chen2020_composite", "Ecker2015", "NCA_Kim2011",
    "OKane2022", "Ramadass2004"
]

available = []
for name in test_sets:
    try:
        params = pybamm.ParameterValues(name)
        print(f"[OK] {name} - Available")
        available.append(name)
    except Exception as e:
        print(f"[X] {name} - Not available: {type(e).__name__}")

print(f"\nTotal available: {len(available)}")
if available:
    print(f"Available sets: {available}")
else:
    print("\n[!] No parameter sets found!")
    print("Try: pip install --upgrade pybamm")
    print("Or: pip install pybamm[all]")

=======
"""Quick script to check PyBaMM parameter set availability"""
import pybamm

print(f"PyBaMM version: {pybamm.__version__}")
print("\nTesting parameter sets...")

test_sets = [
    "Ai2020", "Marquis2019", "Prada2013", "Chen2020",
    "Chen2020_composite", "Ecker2015", "NCA_Kim2011",
    "OKane2022", "Ramadass2004"
]

available = []
for name in test_sets:
    try:
        params = pybamm.ParameterValues(name)
        print(f"[OK] {name} - Available")
        available.append(name)
    except Exception as e:
        print(f"[X] {name} - Not available: {type(e).__name__}")

print(f"\nTotal available: {len(available)}")
if available:
    print(f"Available sets: {available}")
else:
    print("\n[!] No parameter sets found!")
    print("Try: pip install --upgrade pybamm")
    print("Or: pip install pybamm[all]")

>>>>>>> e25e88bc9d309c3e29a000420b6d5c43e3c84787
