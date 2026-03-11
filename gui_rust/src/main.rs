mod app;
mod simulation;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_title("GAIA — Battery Management Simulator")
            .with_inner_size([1440.0, 900.0])
            .with_min_inner_size([900.0, 600.0]),
        ..Default::default()
    };

    eframe::run_native(
        "GAIA Simulator",
        options,
        Box::new(|cc| Ok(Box::new(app::GaiaApp::new(cc)))),
    )
}
