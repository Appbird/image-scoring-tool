use std::path::PathBuf;

use anyhow::Result;
use eframe::{
    egui,
    egui::{Key, Modifiers, TextureHandle},
};

use crate::image_manager::ImageManager;

pub struct ViewerApp {
    pub idx: usize,
    texture: Option<TextureHandle>,
    mgr: ImageManager
}

impl ViewerApp {
    pub fn new(files: Vec<PathBuf>) -> Self {
        let mgr = ImageManager::new(files, 8, 2, (2560, 1440));
        Self {
            idx: 0,
            texture: None,
            mgr
        }
    }

    fn load_current(&mut self, ctx: &egui::Context) -> Result<()> {
        if let Some(t) = &mut self.texture {
            t.set((*img).clone);
        }
    }

    fn next(&mut self, ctx: &egui::Context) {
        if self.files.is_empty() {
            return;
        }
        self.idx = (self.idx + 1) % self.files.len();
        if let Err(e) = self.load_current(ctx) {
            eprintln!("{e:?}");
        }
    }

    fn prev(&mut self, ctx: &egui::Context) {
        if self.files.is_empty() {
            return;
        }
        if self.idx == 0 {
            self.idx = self.files.len() - 1;
        } else {
            self.idx -= 1;
        }
        if let Err(e) = self.load_current(ctx) {
            eprintln!("{e:?}");
        }
    }
}

impl eframe::App for ViewerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // 初回ロード
        if self.texture.is_none() {
            if let Err(e) = self.load_current(ctx) {
                eprintln!("{e:?}");
            }
        }

        // 入力（← / →）
        let left = ctx.input_mut(|i| i.consume_key(Modifiers::NONE, Key::ArrowLeft));
        let right = ctx.input_mut(|i| i.consume_key(Modifiers::NONE, Key::ArrowRight));
        if left {
            self.prev(ctx);
        } else if right {
            self.next(ctx);
        }

        // 画像（フィット表示）
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                if let Some(tex) = &self.texture {
                    let avail = ui.available_size();
                    let tex_size = tex.size_vec2();
                    let scale = (avail.x / tex_size.x)
                        .min(avail.y / tex_size.y)
                        .min(1.0f32.max(f32::MIN_POSITIVE));
                    let size = tex_size * scale;

                    ui.add(egui::Image::from_texture((tex.id(), size)));
                } else {
                    ui.label("画像を読み込み中…");
                }
            });
        });

        // 左上オーバーレイ：ファイル名
        egui::Area::new("filename_overlay".into())
            .anchor(egui::Align2::LEFT_TOP, egui::vec2(8.0, 8.0))
            .movable(false)
            .interactable(false)
            .show(ctx, |ui| {
                egui::Frame::none()
                    .fill(egui::Color32::from_rgba_unmultiplied(0, 0, 0, 140))
                    .rounding(6.0)
                    .inner_margin(egui::Margin::symmetric(8.0, 6.0))
                    .show(ui, |ui| {
                        ui.label(
                            egui::RichText::new(&self.filename)
                                .monospace()
                                .color(egui::Color32::WHITE),
                        );
                    });
            });

        // 下部ヘルプ
        egui::TopBottomPanel::bottom("help_bar")
            .resizable(false)
            .show(ctx, |ui| {
                ui.horizontal_wrapped(|ui| {
                    ui.label("←/→: 前後の画像へ   |   Esc/Q: 終了");
                });
            });

        // 終了ショートカット
        let quit = ctx.input_mut(|i| {
            i.consume_key(Modifiers::NONE, Key::Escape)
                || i.consume_key(Modifiers::NONE, Key::Q)
        });
        if quit {
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }
    }
}
