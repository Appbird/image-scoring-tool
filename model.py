# model.py
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import pygame

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
ID_REGEX = re.compile(r"1-([0-9]{8})-[A-Za-z0-9_]+\.jpg$", re.IGNORECASE)

@dataclass
class Item:
    path: Path
    label: str = ""     # 'o' / 'x' / ''
    comment: str = ""   # free text

def extract_sid(filename: str) -> str:
    m = ID_REGEX.search(filename)
    if m is None:
        print(f"[Warning] ignore file {filename}.", file=sys.stderr)
        return ""
    return m.group(1)

def pick_font(font_path: str | None, size: int) -> pygame.font.Font:
    """
    日本語対応フォントを優先的に選ぶ。
    明示指定(--font) > 候補の順で match_font 。
    """
    if font_path:
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            pass

    # 日本語環境でありがちな候補を順に探索
    candidates = [
        "ヒラギノ角ゴシック W1",
        # macOS
        "Hiragino Sans", "Hiragino Kaku Gothic ProN",
        # Linux / 共通
        "Noto Sans CJK JP", "Noto Sans CJK", "Noto Sans JP",
        "IPAGothic", "IPAexGothic",
        # フォールバック
        "Arial Unicode MS",
    ]
    for name in candidates:
        match = pygame.font.match_font(name)
        if match:
            try:
                return pygame.font.Font(match, size)
            except Exception:
                continue

    # 最後の手段（英数のみの可能性あり）
    return pygame.font.SysFont(None, size)

from pathlib import Path

def read_student_ids(csv_path: Path) -> list[str]:
    """
    1行に1 ID（8桁）を想定。カンマ区切りなら最初のセルを採用。
    空行・コメント(#...)はスキップ。順序は保持。
    """
    ids: list[str] = []
    if not csv_path.exists():
        return ids
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 最初のカンマまでをIDとみなす（純粋に1列だけでもOK）
        token = line.split(",")[0].strip()
        if token.isdigit() and len(token) == 8:
            ids.append(token)
    return ids