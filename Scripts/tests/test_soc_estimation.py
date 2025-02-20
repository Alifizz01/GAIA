from bms_core.soc_estimation import SOCEstimator

def test_soc_estimation():
    ocv_lookup = {
        0: 2.50, 10: 3.00, 20: 3.30, 30: 3.50, 40: 3.65, 50: 3.75,
        60: 3.85, 70: 3.95, 80: 4.05, 90: 4.15, 100: 4.20
    }
    
    estimator = SOCEstimator(initial_soc=75)
    
    # Simulate discharge with 5A over 1 hour
    soc = estimator.update(measured_voltage=3.8, current=5, dt=3600, ocv_lookup=ocv_lookup)
    
    print(f"Updated SOC: {soc:.2f}%")

test_soc_estimation()
