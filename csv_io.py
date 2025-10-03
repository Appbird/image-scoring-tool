# csv_io.py
from pathlib import Path
import csv
from typing import List
from model import Item, extract_sid
# csv_io.py
from typing import List, Dict, Optional
from model import Item, extract_sid

def save_csv(out_csv: Path, items: List[Item],
             ordered_ids: Optional[List[str]] = None,
             include_all_ids: bool = True) -> None:
    """
    ordered_ids が指定されれば、その順で出力。
    include_all_ids=True のとき、itemsに存在しないIDも空行で出す。
    """
    # sid -> item の代表（同一IDに複数ある場合は先頭を採用）
    by_sid: Dict[str, Item] = {}
    for it in items:
        sid = extract_sid(it.path.name)
        if sid and sid not in by_sid:
            by_sid[sid] = it

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "filename", "label", "comment"])

        if ordered_ids:
            for sid in ordered_ids:
                it = by_sid.get(sid)
                if it:
                    w.writerow([sid, it.path.name, it.label, it.comment])
                elif include_all_ids:
                    w.writerow([sid, "", "", ""])  # 見つからないIDも空で出力
        else:
            # フォールバック：items順
            for it in items:
                sid = extract_sid(it.path.name)
                w.writerow([sid, it.path.name, it.label, it.comment])
