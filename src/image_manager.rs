use std::{
    path::{Path, PathBuf},
    sync::Arc,
    thread,
};

use crossbeam_channel::{unbounded, Receiver, Sender};
use image::{imageops::FilterType, DynamicImage, GenericImageView};
use lru::LruCache;
use eframe::egui::ColorImage;


// バックグラウンドからUIに渡すメッセージ
pub enum Msg{
    Decoded { idx: usize, img: Arc<ColorImage> },
    Failed { idx: usize, err: String }
}

pub struct ImageManager {
    files: Vec<PathBuf>,
    rx: Receiver<Msg>,
    tx: Sender<Msg>,
    cache: LruCache<usize, Arc<ColorImage>>,
    prefetch: usize,
    max_size: (u32, u32),
}

impl ImageManager {
    pub fn new(
        files: Vec<PathBuf>,
        cache_capacity: usize,
        prefetch: usize,
        max_size: (u32, u32)
    ) -> Self {
        let (tx, rx) = unbounded();
        Self {
            files, rx, tx, 
            cache: LruCache::new(cache_capacity.try_into().unwrap()),
            prefetch,
            max_size           
        }
    }
    pub fn len(&self) -> usize { self.files.len() }

    pub fn poll(&mut self) -> Vec<usize> {
        let mut updated: Vec<usize> = Vec::new();
        while let Ok(msg) = self.rx.try_recv() {
            match msg {
                Msg::Decoded { idx, img } => {
                    self.cache.put(idx, img);
                    updated.push(idx);
                }
                Msg::Failed { idx, err } => {
                    eprintln!("[ImageManager] failed idx={idx}: {err}")
                }
            }
        }
        updated
    }
    pub fn get(&mut self, idx: usize) -> Option<Arc<ColorImage>>{
        self.cache.get(&idx).cloned()
    }
    
    pub fn request(&mut self, idx: usize) {
        if idx >= self.files.len() || self.cache.contains(&idx) { return; }
        let path = self.files[idx].clone();
        let tx = self.tx.clone();
        let (mw, mh) = self.max_size;
        thread::spawn(move || {
            match decode_resized(&path, mw, mh) {
                Ok(img) => { let _ = tx.send(Msg::Decoded { idx, img: Arc::new(img) }); }
                Err(e) => { let _ = tx.send(Msg::Failed { idx, err: format!("{e:#}") }); }
            }
        });
    }
    pub fn request_with_prefetch(&mut self, idx: usize) {
        if self.files.is_empty() { return; }
        let n = self.files.len();
        
        self.request(idx);
        for off in 1..=self.prefetch {
            self.request((idx + n - off) % n);
            self.request((idx + off) % n);
        }
    }
}

fn decode_resized(
    path:&Path,
    max_w: u32,
    max_h: u32
) -> anyhow::Result<ColorImage> {
    let img = image::open(path)?;
    let (w,h) = img.dimensions();

    let scale = (max_w as f32 / w as f32).min(max_h as f32 / h as f32).min(1.0);
    let dynimg: DynamicImage = if scale < 1.0 {
        let nw = (w as f32 * scale).max(1.0) as u32;
        let nh = (h as f32 * scale).max(1.0) as u32;
        img.resize(nw, nh, FilterType::Triangle)
    } else {
        img
    };

    let rgba = dynimg.to_rgba8();
    Ok(ColorImage::from_rgba_unmultiplied(
        [rgba.width() as usize, rgba.height() as usize],
        rgba.as_raw()
    ))
}