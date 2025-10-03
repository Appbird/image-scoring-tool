use std::path::PathBuf;
use clap::Parser;

/// 画像ビューワ: フォルダ内の画像を ←/→ で閲覧
#[derive(Parser, Debug)]
#[command(version, about)]
pub struct Args {
    /// 画像フォルダのパス
    pub folder: PathBuf,

    /// サブフォルダも再帰的に探索する（デフォルト:しない）
    #[arg(long)]
    pub recursive: bool,
}
