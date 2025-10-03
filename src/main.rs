mod args;
mod image_list;
mod viewer;
mod image_manager;

use anyhow::{anyhow, Result};
use args::Args;
use clap::Parser;
use eframe::egui;
use image_list::collect_images;
use viewer::ViewerApp;

fn main() -> Result<()> {
    let args = Args::parse();
    let files = collect_images(&args.folder, args.recursive)?;

    let native_options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("imgviewer")
            .with_inner_size([1000.0, 700.0]),
        ..Default::default()
    };

    eframe::run_native(
        "imgviewer",
        native_options,
        Box::new(|_cc| Ok(Box::new(ViewerApp::new(files)))),
    )
    .map_err(|e| anyhow!("アプリ起動に失敗しました: {e}"))?;

    Ok(())
}
