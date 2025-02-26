import json

def save_experiment(self, filename="experiment_profile.json"):
    """Saves the current experiment profile to a JSON file."""
    
    experiment_data = {
        "experiment_steps": [
            "Discharge at C/10 for 10 hours or until 3.3 V",
            "Rest for 1 hour",
            "Charge at 1 A until 4.1 V",
            "Hold at 4.1 V until 50 mA",
            "Rest for 1 hour"
        ],
        "repeat": 3
    }

    with open(filename, "w") as json_file:
        json.dump(experiment_data, json_file, indent=4)

    print(f"Experiment profile saved to {filename}")
