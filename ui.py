# ui.py
from typing import List, Tuple
import pygame
from pygame import Rect
from model import Item, extract_sid

# 色
COL_BG = (16, 16, 16)
COL_PANEL = (0, 0, 0, 160)
COL_TEXT = (255, 255, 255)
COL_TEXT_DIM = (200, 200, 200)
COL_OK = (80, 200, 120)
COL_NG = (230, 90, 90)
COL_SEL = (60, 90, 160, 140)

def draw_panel(surface: pygame.Surface, rect: Rect, color=COL_PANEL):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(color)
    surface.blit(panel, rect.topleft)

def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color, pos: Tuple[int,int]):
    surface.blit(font.render(text, True, color), pos)

def draw_multiline(surface, lines: List[str], font, color, pos=(10,10), line_gap=6):
    x, y = pos
    for ln in lines:
        img = font.render(ln, True, color)
        surface.blit(img, (x, y))
        y += img.get_height() + line_gap

class Sidebar:
    """
    右側に一覧（ファイル名 / o,x / コメント）を表示。
    - 固定幅
    - スクロール（ホイール / PgUp PgDn / Home End）
    - クリックで移動
    """
    def __init__(self, width: int = 420, row_h: int | None = None, padding: int = 10):
        self.width = width
        self.padding = padding
        self.scroll = 0
        # row_h は後でフォント決定後に set_row_height() で設定する想定
        self.row_h = row_h or 56  # 一旦デフォ
    # ui.py に追加: フォントに合わせて動的に行高を設定
    def set_row_height(self, font: pygame.font.Font, font_small: pygame.font.Font, lines_per_item: int = 2):
        # CJKは get_height() より get_linesize() が安全
        base = max(font.get_linesize(), font_small.get_linesize())
        # 2行構成なので行数分を確保 + ちょい余白
        self.row_h = lines_per_item * base + 8
    def get_rect(self, screen: pygame.Surface) -> Rect:
        sw, sh = screen.get_size()
        return Rect(sw - self.width, 0, self.width, sh)

    def visible_count(self, rect: Rect, header_h: int) -> int:
        avail = rect.height - header_h - self.padding
        return max(0, avail // self.row_h)

    def clamp_scroll(self, items_len: int, vis: int):
        max_scroll = max(0, items_len - vis)
        self.scroll = max(0, min(self.scroll, max_scroll))

    def handle_wheel(self, y: int):
        # y>0 で上スクロール、y<0 で下スクロール
        self.scroll = max(0, self.scroll - y)

    def handle_pgup(self, vis: int):
        self.scroll = max(0, self.scroll - vis)

    def handle_pgdn(self, items_len: int, vis: int):
        self.scroll = min(max(0, items_len - vis), self.scroll + vis)

    def handle_home(self):
        self.scroll = 0

    def handle_end(self, items_len: int, vis: int):
        self.scroll = max(0, items_len - vis)

    def click_to_index(self, pos: Tuple[int,int], rect: Rect, header_h: int, items_len: int) -> int | None:
        x, y = pos
        if not rect.collidepoint(x, y):
            return None
        rel_y = y - (header_h + self.padding)
        if rel_y < 0:
            return None
        row = rel_y // self.row_h
        idx = self.scroll + int(row)
        if 0 <= idx < items_len:
            return idx
        return None

    def ensure_visible(self, index: int, items_len: int, vis: int):
        """
        現在の self.scroll を、index(選択行) が画面内に入るよう補正する。
        vis は可視行数。
        """
        if vis <= 0 or items_len <= 0:
            return

        # 画面の先頭/末尾インデックス
        top = self.scroll
        bottom = self.scroll + vis - 1

        if index < top:
            # 選択が上に見切れている → 先頭に合わせる
            self.scroll = index
        elif index > bottom:
            # 選択が下に見切れている → 末尾に合わせる
            self.scroll = index - vis + 1

        # 範囲クリップ
        max_scroll = max(0, items_len - vis)
        self.scroll = max(0, min(self.scroll, max_scroll))

    def draw(self, screen: pygame.Surface, items: List[Item], font: pygame.font.Font,
             font_small: pygame.font.Font, current_idx: int):
        rect = self.get_rect(screen)
        draw_panel(screen, rect)

        # ヘッダ
        header_lines = ["一覧 (クリックで移動 / ホイールでスクロール)",
                        "filename  |  label  |  comment"]
        header_h = 2 * (font.get_height() + 6) + self.padding
        draw_multiline(screen, header_lines, font, COL_TEXT, pos=(rect.x + self.padding, rect.y + self.padding))

        vis = self.visible_count(rect, header_h)
        self.clamp_scroll(len(items), vis)

        y = rect.y + header_h
        x = rect.x + self.padding

        # 各行
        for i in range(self.scroll, min(len(items), self.scroll + vis)):
            it = items[i]

            # 選択行の薄いハイライト
            if i == current_idx:
                sel_rect = Rect(rect.x + 2, y + 2, rect.width - 4, self.row_h - 4)
                draw_panel(screen, sel_rect, COL_SEL)

            # label色
            if it.label == "o":
                lab_col = COL_OK
            elif it.label == "x":
                lab_col = COL_NG
            else:
                lab_col = COL_TEXT_DIM

            # 表示文字（短縮）
            fname = it.path.name
            if len(fname) > 38:
                fname = fname[:35] + "..."
            cmt = it.comment.replace("\n", " ")
            if len(cmt) > 28:
                cmt = cmt[:25] + "..."

            line = f"{fname}"
            draw_text(screen, line, font, COL_TEXT, (x, y + 4))
            # 2列目: label
            draw_text(screen, f"[{it.label or ' '}]",
                      font, lab_col, (x, y + 4 + font.get_height() + 2))
            # 3列目: comment
            draw_text(screen, cmt, font_small, COL_TEXT_DIM,
                      (x + 120, y + 6 + font.get_height() + 2))

            y += self.row_h
