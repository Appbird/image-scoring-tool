use std::{ffi::OsStr, path::{Path, PathBuf}};
use anyhow::{anyhow, Result};
use walkdir::WalkDir;

fn is_image_path(p: &Path) -> bool {
    static EXT: &[&str] = &["png", "jpg", "jpeg", "bmp", "gif", "webp", "tif", "tiff"];
    p.extension()
        .and_then(OsStr::to_str)
        .map(|e| EXT.iter().any(|x| e.eq_ignore_ascii_case(x)))
        .unwrap_or(false)
}

pub fn collect_images(root: &Path, recursive: bool) -> Result<Vec<PathBuf>> {
    if !root.exists() || !root.is_dir() {
        return Err(anyhow!(
            "指定フォルダが見つからないか、ディレクトリではありません: {}",
            root.display()
        ));
    }

    let iter: Box<dyn Iterator<Item = walkdir::DirEntry>> = if recursive {
        Box::new(WalkDir::new(root).into_iter().flatten())
    } else {
        Box::new(WalkDir::new(root).max_depth(1).into_iter().flatten())
    };

    let mut files: Vec<PathBuf> = iter
        .filter(|e| e.file_type().is_file())
        .map(|e| e.path().to_path_buf())
        .filter(|p| is_image_path(p))
        .collect();

    files.sort();
    if files.is_empty() {
        return Err(anyhow!("画像ファイルが見つかりませんでした: {}", root.display()));
    }
    Ok(files)
}
