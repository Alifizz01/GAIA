use serde::{Deserialize, Serialize};
use std::process::Command;

/// Parameters sent to the Python simulation runner.
#[derive(Debug, Clone, Serialize)]
pub struct SimulationParams {
    pub model_type: String,
    pub chemistry: String,
    pub initial_temperature: f64,
    pub duration: u64,
    pub simulation_mode: String,
}

/// Result returned by the Python simulation runner.
#[derive(Debug, Clone, Deserialize, Default)]
pub struct SimulationResult {
    pub success: bool,
    #[serde(default)]
    pub time: Vec<f64>,
    #[serde(default)]
    pub voltage: Vec<f64>,
    #[serde(default)]
    pub soc: Vec<f64>,
    #[serde(default)]
    pub temperature: Vec<f64>,
    #[serde(default)]
    pub current: Vec<f64>,
    pub error: Option<String>,
}

/// Spawn `python3 <script_path> --params <json>` and parse the result.
/// The Python script prints `GAIA_RESULT:{json}` on one line.
pub fn run_simulation(params: &SimulationParams, script_path: &str) -> SimulationResult {
    let params_json = match serde_json::to_string(params) {
        Ok(j) => j,
        Err(e) => {
            return SimulationResult {
                success: false,
                error: Some(format!("Failed to serialize params: {e}")),
                ..Default::default()
            }
        }
    };

    // Try python3 first, fall back to python
    let interpreters = ["python3", "python"];
    let mut last_err = String::new();

    for interpreter in interpreters {
        let result = Command::new(interpreter)
            .arg(script_path)
            .arg("--params")
            .arg(&params_json)
            .output();

        match result {
            Ok(out) => {
                let stdout = String::from_utf8_lossy(&out.stdout);
                let stderr = String::from_utf8_lossy(&out.stderr);

                // Find the tagged result line
                for line in stdout.lines() {
                    if let Some(json_str) = line.strip_prefix("GAIA_RESULT:") {
                        return match serde_json::from_str::<SimulationResult>(json_str) {
                            Ok(r) => r,
                            Err(e) => SimulationResult {
                                success: false,
                                error: Some(format!(
                                    "JSON parse error: {e}\nRaw: {}",
                                    &json_str[..json_str.len().min(300)]
                                )),
                                ..Default::default()
                            },
                        };
                    }
                }

                // No GAIA_RESULT line found
                return SimulationResult {
                    success: false,
                    error: Some(format!(
                        "No GAIA_RESULT line in output.\nstdout: {}\nstderr: {}",
                        &stdout[..stdout.len().min(500)],
                        &stderr[..stderr.len().min(500)],
                    )),
                    ..Default::default()
                };
            }
            Err(e) => {
                last_err = format!("'{}' not found: {e}", interpreter);
                continue;
            }
        }
    }

    SimulationResult {
        success: false,
        error: Some(format!(
            "Could not launch Python interpreter. {last_err}\n\
             Make sure Python 3 is installed and on PATH."
        )),
        ..Default::default()
    }
}
