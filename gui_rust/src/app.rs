use eframe::egui::{self, Color32, RichText, Ui, Vec2};
use egui_plot::{Legend, Line, Plot, PlotPoints};
use std::sync::{Arc, Mutex};
use std::thread;

use crate::simulation::{run_simulation, SimulationParams, SimulationResult};

// ─── Palette ──────────────────────────────────────────────────────────────────

const COL_ACCENT: Color32 = Color32::from_rgb(90, 190, 255);
const COL_GREEN: Color32 = Color32::from_rgb(72, 210, 130);
const COL_YELLOW: Color32 = Color32::from_rgb(255, 190, 70);
const COL_RED: Color32 = Color32::from_rgb(240, 80, 80);
const COL_PANEL: Color32 = Color32::from_rgb(28, 30, 36);
const COL_SECTION: Color32 = Color32::from_rgb(140, 200, 255);

// Plot line colours
const PLOT_VOLTAGE: Color32 = Color32::from_rgb(90, 190, 255);
const PLOT_SOC: Color32 = Color32::from_rgb(72, 210, 130);
const PLOT_CURRENT: Color32 = Color32::from_rgb(255, 190, 70);
const PLOT_TEMP: Color32 = Color32::from_rgb(240, 100, 100);

// ─── Status ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum SimStatus {
    Idle,
    Running,
    Done,
    Error(String),
}

// ─── App state ────────────────────────────────────────────────────────────────

pub struct GaiaApp {
    // Configuration selectors (indices into option arrays)
    sim_mode_idx: usize,   // Manual / Experiment
    model_idx: usize,      // SPM / SPMe / DFN
    chemistry_idx: usize,  // NMC / LFP / NCA
    cell_cfg_idx: usize,   // 6s74p … 16s1p
    charge_mode_idx: usize, // Charging / Discharging

    // Numeric parameters
    c_rate: f32,        // 0.1 – 5.0
    voltage: f32,       // 20 – 40 V
    sim_time: String,   // seconds (text)
    init_temp: String,  // °C (text)

    // Runtime
    status: SimStatus,
    result: Arc<Mutex<Option<SimulationResult>>>,
    script_path: String,
}

impl GaiaApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        // Apply dark theme once at startup
        let mut vis = egui::Visuals::dark();
        vis.window_rounding = egui::Rounding::same(8.0);
        vis.panel_fill = COL_PANEL;
        cc.egui_ctx.set_visuals(vis);

        Self {
            sim_mode_idx: 0,
            model_idx: 0,
            chemistry_idx: 0,
            cell_cfg_idx: 4, // default "16s1p"
            charge_mode_idx: 1, // default Discharging
            c_rate: 1.0,
            voltage: 30.0,
            sim_time: "3600".into(),
            init_temp: "25".into(),
            status: SimStatus::Idle,
            result: Arc::new(Mutex::new(None)),
            script_path: Self::find_script(),
        }
    }

    /// Search for the Python runner script in typical locations.
    fn find_script() -> String {
        let candidates = [
            "Scripts/run_simulation.py",
            "../Scripts/run_simulation.py",
            "../../Scripts/run_simulation.py",
        ];
        for c in &candidates {
            if std::path::Path::new(c).exists() {
                return c.to_string();
            }
        }
        // Absolute fallback
        "/home/user/GAIA/Scripts/run_simulation.py".to_string()
    }

    // ── Simulation control ───────────────────────────────────────────────────

    fn start(&mut self) {
        if self.status == SimStatus::Running {
            return;
        }

        const MODEL_TYPES: [&str; 3] = ["SPM", "SPMe", "DFN"];
        const CHEMISTRIES: [&str; 3] = ["NMC", "LFP", "NCA"];
        const SIM_MODES: [&str; 2] = ["Manual Parameter Mode", "Experiment Mode"];

        let duration: u64 = self.sim_time.trim().parse().unwrap_or(3600);
        let temp_c: f64 = self.init_temp.trim().parse().unwrap_or(25.0);
        let initial_temperature = if temp_c < 100.0 { temp_c + 273.15 } else { temp_c };

        let params = SimulationParams {
            model_type: MODEL_TYPES[self.model_idx].into(),
            chemistry: CHEMISTRIES[self.chemistry_idx].into(),
            initial_temperature,
            duration,
            simulation_mode: SIM_MODES[self.sim_mode_idx].into(),
        };

        let result_arc = Arc::clone(&self.result);
        let script = self.script_path.clone();

        self.status = SimStatus::Running;
        *self.result.lock().unwrap() = None;

        thread::spawn(move || {
            let r = run_simulation(&params, &script);
            *result_arc.lock().unwrap() = Some(r);
        });
    }

    fn stop(&mut self) {
        // We can't interrupt the subprocess easily; just mark idle.
        // The thread will finish and we ignore the result.
        self.status = SimStatus::Idle;
    }

    fn reset(&mut self) {
        self.status = SimStatus::Idle;
        *self.result.lock().unwrap() = None;
    }

    /// Poll the shared result on every frame while running.
    fn poll_result(&mut self) {
        if self.status != SimStatus::Running {
            return;
        }
        if let Ok(guard) = self.result.try_lock() {
            if let Some(ref r) = *guard {
                self.status = if r.success {
                    SimStatus::Done
                } else {
                    SimStatus::Error(r.error.clone().unwrap_or_else(|| "Unknown error".into()))
                };
            }
        }
    }

    // ── Left control panel ───────────────────────────────────────────────────

    fn draw_sidebar(&mut self, ui: &mut Ui) {
        ui.add_space(12.0);
        ui.label(
            RichText::new("⚡  GAIA Simulator")
                .strong()
                .size(18.0)
                .color(COL_ACCENT),
        );
        ui.label(
            RichText::new("Battery Management System")
                .small()
                .color(Color32::GRAY),
        );
        ui.add_space(8.0);
        ui.separator();
        ui.add_space(6.0);

        // ── Configuration ────────────────────────────────────────────────────
        section_header(ui, "Configuration");

        let editing = self.status != SimStatus::Running;

        combo(ui, "Mode", &mut self.sim_mode_idx, &["Manual", "Experiment"], "sim_mode", editing);
        combo(ui, "Model", &mut self.model_idx, &["SPM", "SPMe", "DFN"], "model", editing);
        combo(
            ui,
            "Chemistry",
            &mut self.chemistry_idx,
            &["NMC", "LFP", "NCA"],
            "chemistry",
            editing,
        );
        combo(
            ui,
            "Cell Config",
            &mut self.cell_cfg_idx,
            &["6s74p", "8s24p", "12s48p", "14s96p", "16s1p"],
            "cell_cfg",
            editing,
        );
        combo(
            ui,
            "Charge Mode",
            &mut self.charge_mode_idx,
            &["Charging", "Discharging"],
            "charge_mode",
            editing,
        );

        ui.add_space(8.0);
        ui.separator();
        ui.add_space(6.0);

        // ── Parameters ───────────────────────────────────────────────────────
        section_header(ui, "Parameters");

        labeled_slider(ui, "C-Rate", &mut self.c_rate, 0.1..=5.0, editing, |v| {
            format!("{v:.1} C")
        });
        labeled_slider(ui, "Voltage", &mut self.voltage, 20.0..=40.0, editing, |v| {
            format!("{v:.0} V")
        });

        ui.add_space(4.0);
        labeled_text(ui, "Simulation Time (s)", &mut self.sim_time, "e.g. 3600", editing);
        labeled_text(ui, "Temperature (°C)", &mut self.init_temp, "e.g. 25", editing);

        ui.add_space(8.0);
        ui.separator();
        ui.add_space(6.0);

        // ── Control buttons ──────────────────────────────────────────────────
        section_header(ui, "Control");
        ui.add_space(4.0);
        ui.horizontal(|ui| {
            let running = self.status == SimStatus::Running;

            if ui
                .add_enabled(
                    !running,
                    egui::Button::new(RichText::new("▶  Start").color(COL_GREEN))
                        .min_size(Vec2::new(76.0, 30.0)),
                )
                .clicked()
            {
                self.start();
            }

            if ui
                .add_enabled(
                    running,
                    egui::Button::new(RichText::new("⏹  Stop").color(COL_RED))
                        .min_size(Vec2::new(76.0, 30.0)),
                )
                .clicked()
            {
                self.stop();
            }

            if ui
                .add(
                    egui::Button::new(RichText::new("↺  Reset").color(COL_YELLOW))
                        .min_size(Vec2::new(76.0, 30.0)),
                )
                .clicked()
            {
                self.reset();
            }
        });

        ui.add_space(8.0);
        ui.separator();
        ui.add_space(6.0);

        // ── Status ───────────────────────────────────────────────────────────
        section_header(ui, "Status");
        ui.add_space(4.0);

        match &self.status.clone() {
            SimStatus::Idle => {
                ui.label(RichText::new("● Idle").color(Color32::GRAY));
            }
            SimStatus::Running => {
                ui.horizontal(|ui| {
                    ui.spinner();
                    ui.label(RichText::new("Running…").color(COL_ACCENT));
                });
            }
            SimStatus::Done => {
                ui.label(RichText::new("● Complete").color(COL_GREEN));
            }
            SimStatus::Error(msg) => {
                ui.label(RichText::new("● Error").color(COL_RED));
                egui::ScrollArea::vertical()
                    .max_height(120.0)
                    .id_source("err_scroll")
                    .show(ui, |ui| {
                        ui.label(
                            RichText::new(msg.as_str())
                                .small()
                                .color(Color32::from_rgb(255, 120, 120)),
                        );
                    });
            }
        }

        // Separator + script path hint
        ui.add_space(8.0);
        ui.separator();
        ui.add_space(4.0);
        ui.label(
            RichText::new(format!("Script: {}", self.script_path))
                .small()
                .color(Color32::DARK_GRAY),
        );
    }

    // ── Plot area ────────────────────────────────────────────────────────────

    fn draw_plots(&mut self, ui: &mut Ui) {
        // Snapshot the result (release lock before UI work)
        let snapshot: Option<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> = {
            let guard = self.result.lock().unwrap();
            guard.as_ref().and_then(|r| {
                if r.success {
                    Some((
                        r.time.clone(),
                        r.voltage.clone(),
                        r.soc.clone(),
                        r.temperature.clone(),
                        r.current.clone(),
                    ))
                } else {
                    None
                }
            })
        };

        let empty: Vec<f64> = Vec::new();
        let (time, voltage, soc, temperature, current) = match &snapshot {
            Some((t, v, s, temp, c)) => (t, v, s, temp, c),
            None => (&empty, &empty, &empty, &empty, &empty),
        };

        let total_h = ui.available_height();
        let total_w = ui.available_width();
        let half_h = (total_h / 2.0) - 14.0;
        let half_w = (total_w / 2.0) - 8.0;

        ui.horizontal(|ui| {
            // Left column
            ui.vertical(|ui| {
                draw_plot(
                    ui, "Voltage vs Time", "Time (s)", "Voltage (V)",
                    time, voltage, PLOT_VOLTAGE, half_w, half_h,
                );
                ui.add_space(8.0);
                draw_plot(
                    ui, "Current vs Time", "Time (s)", "Current (A)",
                    time, current, PLOT_CURRENT, half_w, half_h,
                );
            });

            ui.add_space(8.0);

            // Right column
            ui.vertical(|ui| {
                draw_plot(
                    ui, "SOC vs Time", "Time (s)", "SOC (%)",
                    time, soc, PLOT_SOC, half_w, half_h,
                );
                ui.add_space(8.0);
                draw_plot(
                    ui, "Temperature vs Time", "Time (s)", "Temperature (K)",
                    time, temperature, PLOT_TEMP, half_w, half_h,
                );
            });
        });
    }
}

// ─── eframe::App impl ────────────────────────────────────────────────────────

impl eframe::App for GaiaApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.poll_result();

        // Keep repainting at ~5 fps while a simulation is running
        if self.status == SimStatus::Running {
            ctx.request_repaint_after(std::time::Duration::from_millis(200));
        }

        // Left sidebar
        egui::SidePanel::left("sidebar")
            .resizable(false)
            .exact_width(290.0)
            .frame(egui::Frame::default().fill(COL_PANEL).inner_margin(8.0))
            .show(ctx, |ui| {
                egui::ScrollArea::vertical().show(ui, |ui| {
                    self.draw_sidebar(ui);
                });
            });

        // Main plot area
        egui::CentralPanel::default().show(ctx, |ui| {
            self.draw_plots(ui);
        });
    }
}

// ─── Free helper functions ───────────────────────────────────────────────────

fn section_header(ui: &mut Ui, label: &str) {
    ui.label(RichText::new(label).strong().color(COL_SECTION));
    ui.add_space(2.0);
}

fn combo(
    ui: &mut Ui,
    label: &str,
    idx: &mut usize,
    options: &[&str],
    id: &str,
    enabled: bool,
) {
    ui.add_enabled_ui(enabled, |ui| {
        ui.horizontal(|ui| {
            ui.label(format!("{label}:"));
            egui::ComboBox::from_id_source(id)
                .width(158.0)
                .selected_text(options[*idx])
                .show_ui(ui, |ui| {
                    for (i, opt) in options.iter().enumerate() {
                        ui.selectable_value(idx, i, *opt);
                    }
                });
        });
    });
    ui.add_space(2.0);
}

fn labeled_slider(
    ui: &mut Ui,
    label: &str,
    value: &mut f32,
    range: std::ops::RangeInclusive<f32>,
    enabled: bool,
    fmt: impl Fn(f32) -> String,
) {
    ui.add_enabled_ui(enabled, |ui| {
        ui.label(format!("{label}: {}", fmt(*value)));
        ui.add(egui::Slider::new(value, range).show_value(false));
        ui.add_space(2.0);
    });
}

fn labeled_text(ui: &mut Ui, label: &str, value: &mut String, hint: &str, enabled: bool) {
    ui.label(format!("{label}:"));
    ui.add_enabled(
        enabled,
        egui::TextEdit::singleline(value)
            .desired_width(260.0)
            .hint_text(hint),
    );
    ui.add_space(4.0);
}

/// Render a single labelled egui_plot with optional data.
fn draw_plot(
    ui: &mut Ui,
    title: &str,
    _xlabel: &str,
    _ylabel: &str,
    x_data: &[f64],
    y_data: &[f64],
    color: Color32,
    width: f32,
    height: f32,
) {
    // Small bold title above the plot
    ui.label(RichText::new(title).strong().small().color(color));

    let points: PlotPoints = x_data
        .iter()
        .zip(y_data.iter())
        .map(|(&x, &y)| [x, y])
        .collect();

    let line = Line::new(points)
        .color(color)
        .width(2.0)
        .name(title);

    Plot::new(title)
        .height(height - 18.0)
        .min_size(Vec2::new(width, height - 18.0))
        .allow_zoom(true)
        .allow_drag(true)
        .legend(Legend::default())
        .label_formatter(move |_name, val| {
            format!("t = {:.1} s\nval = {:.4}", val.x, val.y)
        })
        .show(ui, |plot_ui| {
            if !x_data.is_empty() {
                plot_ui.line(line);
            }
        });
}
