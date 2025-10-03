# app.py
import argparse
import sys
from pathlib import Path
from typing import List

import pygame
from pygame import Rect

from model import Item, IMAGE_EXTS, extract_sid, pick_font
from image_loader import load_image_as_surface
from csv_io import save_csv
from ui import COL_BG, COL_TEXT, COL_TEXT_DIM, draw_panel, draw_multiline, Sidebar

from model import read_student_ids
from model import extract_sid

def parse_args():
    ap = argparse.ArgumentParser(description="pygame画像ラベラー（右サイドバー付き）")
    ap.add_argument("folder", help="画像フォルダ（直下のみ対象）")
    ap.add_argument("-o", "--output", default=None, help="出力CSVパス（未指定: <folder>/ratings.csv）")
    ap.add_argument("--width", type=int, default=1400, help="ウィンドウ幅（既定: 1400）")
    ap.add_argument("--height", type=int, default=900, help="ウィンドウ高さ（既定: 900）")
    ap.add_argument("--font-size", type=int, default=18, help="UIフォントサイズ（既定: 16）")
    ap.add_argument("--font", type=str, default=None, help="フォントTTF/OTFパス（Noto/IPA等を推奨）")
    ap.add_argument("--sidebar-width", type=int, default=420, help="右サイドバー幅（既定: 420）")
    ap.add_argument("--students", type=str, default=None, help="学籍番号リストCSV（1行1ID）")
    return ap.parse_args()

def main():
    args = parse_args()
    
    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"フォルダが見つかりません: {folder}", file=sys.stderr)
        sys.exit(1)

    out_csv = Path(args.output) if args.output else (folder / "ratings.csv")

    files = [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if not files:
        print("対象画像がありません。", file=sys.stderr)
        sys.exit(1)
    allowed_ids: list[str] = []
    if args.students:
        allowed_ids = read_student_ids(Path(args.students))
    order = {sid: i for i, sid in enumerate(allowed_ids)} if allowed_ids else {}
    if allowed_ids:
        files = [p for p in files if extract_sid(p.name) in order]
    def sort_key(p):
        sid = extract_sid(p.name)
        return order.get(sid, 10**9), p.name  # 同一IDに複数ファイルがあっても安定
    files = sorted(files, key=sort_key)
    assert len(files) > 0

    items: List[Item] = [Item(p) for p in files]
    idx = 0
    comment_mode = False
    comment_buf = ""

    pygame.init()
    pygame.display.set_caption("Image Rater (o/x/c, ←/→, q:保存終了)")
    
    screen = pygame.display.set_mode((args.width, args.height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    font = pick_font(args.font, args.font_size)
    font_small = pick_font(args.font, max(12, args.font_size - 4))

    sidebar = Sidebar(width=args.sidebar_width, row_h=args.font_size + 12)
    sidebar.set_row_height(font, font_small, lines_per_item=2) 

    cur_image_surface = None

    def left_area_rect() -> Rect:
        sw, sh = screen.get_size()
        return Rect(0, 0, sw - sidebar.width, sh)

    def load_current_image():
        nonlocal cur_image_surface
        la = left_area_rect()
        # 上部情報パネル分の少しのマージンを差し引いて縮小
        fit_w = max(100, la.width - 40)
        fit_h = max(100, la.height - 140)
        try:
            cur_image_surface = load_image_as_surface(items[idx].path, (fit_w, fit_h))
            pygame.display.set_caption(f"Image Rater - {items[idx].path.name}")
        except Exception as e:
            items[idx].comment = (items[idx].comment + f" [READ ERROR: {e}]").strip()
            goto_next()

    def goto_prev():
        nonlocal idx
        if idx > 0:
            idx -= 1
            load_current_image()

    def goto_next():
        nonlocal idx
        if idx < len(items) - 1:
            idx += 1
            load_current_image()
            update_sidebar_visibility_for_index()  # ← 追加

    def all_labeled() -> bool:
        return all(it.label in {"o", "x"} for it in items)

    def update_sidebar_visibility_for_index():
        rect_sb = sidebar.get_rect(screen)
        header_h = 2 * (font.get_height() + 6) + sidebar.padding
        vis = sidebar.visible_count(rect_sb, header_h)
        sidebar.ensure_visible(idx, items_len=len(items), vis=vis)

    def on_terminated():
        nonlocal running
        save_csv(out_csv, items, ordered_ids=allowed_ids if allowed_ids else None, include_all_ids=True)
        running = False
    
    # 初回読み込み
    assert len(items) > 0
    load_current_image()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: on_terminated()

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                load_current_image()

            elif event.type == pygame.MOUSEWHEEL:
                # サイドバーをスクロール
                sidebar.handle_wheel(event.y)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # サイドバークリックで移動
                rect_sb = sidebar.get_rect(screen)
                header_h = 2 * (font.get_height() + 6) + sidebar.padding
                to_idx = sidebar.click_to_index(event.pos, rect_sb, header_h, len(items))
                if to_idx is not None:
                    idx = to_idx
                    load_current_image()

            elif event.type == pygame.KEYDOWN:
                if comment_mode:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        items[idx].comment = comment_buf.strip()
                        comment_buf = ""
                        comment_mode = False
                    elif event.key == pygame.K_ESCAPE:
                        comment_buf = ""
                        comment_mode = False
                    elif event.key == pygame.K_BACKSPACE:
                        comment_buf = comment_buf[:-1]
                    else:
                        if event.unicode and event.unicode not in ("\x00", "\r", "\n"):
                            comment_buf += event.unicode
                else:
                    if event.key == pygame.K_q:
                        on_terminated()
                    elif event.key == pygame.K_o:
                        items[idx].label = "o"
                        if idx < len(items) - 1:
                            goto_next()
                        elif all_labeled():
                            on_terminated()
                    elif event.key == pygame.K_x:
                        items[idx].label = "x"
                        if idx < len(items) - 1:
                            goto_next()
                        elif all_labeled():
                            on_terminated()
                    elif event.key == pygame.K_c:
                        comment_mode = True
                        comment_buf = items[idx].comment or ""
                    elif event.key == pygame.K_RIGHT:
                        goto_next()
                    elif event.key == pygame.K_LEFT:
                        goto_prev()
                    elif event.key == pygame.K_PAGEUP:
                        sidebar.handle_pgup(vis=10)
                    elif event.key == pygame.K_PAGEDOWN:
                        sidebar.handle_pgdn(items_len=len(items), vis=10)
                    elif event.key == pygame.K_HOME:
                        sidebar.handle_home()
                    elif event.key == pygame.K_END:
                        sidebar.handle_end(items_len=len(items), vis=10)

        # ===== 描画 =====
        screen.fill(COL_BG)

        # 左（画像＋情報）
        la = left_area_rect()
        if cur_image_surface:
            iw, ih = cur_image_surface.get_size()
            x = la.x + (la.width - iw) // 2
            y = la.y + (la.height - ih) // 2 + 40  # 上に情報パネルを置く分下げる
            screen.blit(cur_image_surface, (x, y))
        
        # 上部情報パネル
        it = items[idx]
        sid = extract_sid(it.path.name) or "(not matched)"
        header_lines = [
            f"[{idx+1}/{len(items)}] {it.path.name}",
            f"student_id: {sid} | label: {it.label or '(none)'} | comment: {it.comment or '(none)'}",
            "操作: o=○, x=×, c=コメント, ←/→=移動, PgUp/PgDn=一覧スクロール, q=保存終了",
        ]
        panel_w = min(la.width - 20, 1200)
        panel_h = (len(header_lines) * (font.get_height() + 6)) + 16
        draw_panel(screen, Rect(la.x + 10, la.y + 10, panel_w, panel_h))
        draw_multiline(screen, header_lines, font, COL_TEXT, pos=(la.x + 18, la.y + 18), line_gap=6)

        # 右サイドバー
        sidebar.draw(screen, items, font, font_small, current_idx=idx)

        # 下部ステータス
        draw_multiline(
            screen,
            [f"保存先: {str(out_csv)}",
             f"フォント: {args.font or 'auto-detected'}"],
            font_small, COL_TEXT_DIM,
            pos=(la.x + 12, screen.get_height() - (font_small.get_height()*2 + 18)),
            line_gap=4
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print(f"CSVを書き出しました: {out_csv}")

if __name__ == "__main__":
    main()
