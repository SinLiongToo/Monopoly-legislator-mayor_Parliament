"""
rename_priso_pdfs_by_target_order.py
=====================================
根據 target_officers.json 的順序，替 downloads_priso/ 內的 PDF 補上官員的全局編號前綴。

命名規則（新）：
  {零補位編號}_{姓名}_財產申報_{申報期次}.pdf
  例：0007_張善政_財產申報_1.pdf

只要資料夾中已有「{姓名}_財產申報_*.pdf」格式的檔案，就會自動加上對應的編號。
若已是「XXXX_姓名_…」格式則跳過（避免重複加號）。

用法：
  python rename_priso_pdfs_by_target_order.py          # 預覽模式（dry-run），不真正改名
  python rename_priso_pdfs_by_target_order.py --apply  # 實際執行改名
"""

import os
import sys
import json
import re

# ── 設定 ──────────────────────────────────────────────────────────────────────
TARGET_OFFICERS_FILE = "target_officers.json"
PRISO_DOWNLOAD_DIR   = "./downloads_priso"

# 要過濾掉的非真實姓名（與 download 腳本相同的邏輯）
SKIP_KEYWORDS = ["2330", "2882", "2317", "股", "公司", "3006"]
# ──────────────────────────────────────────────────────────────────────────────


def should_skip(name: str) -> bool:
    return any(k in name for k in SKIP_KEYWORDS)


def build_officer_index(officers: list) -> dict[str, int]:
    """
    回傳 {name: 全局編號(1-based)} 的字典。
    編號只計算「真實官員」（過濾掉股票/公司名稱），
    但原始 list 順序仍以 target_officers.json 為準。
    """
    index: dict[str, int] = {}
    counter = 1
    for o in officers:
        name = o.get("name", "").strip()
        if name and not should_skip(name):
            if name not in index:          # 若有重複姓名只給同一號
                index[name] = counter
            counter += 1
    return index


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("⚠️  [預覽模式] 不會真正改名。加上 --apply 才會執行。\n")
    else:
        print("🚀 [執行模式] 即將改名 downloads_priso/ 內的 PDF 檔案。\n")

    # 讀取官員名冊
    if not os.path.exists(TARGET_OFFICERS_FILE):
        print(f"❌ 找不到 {TARGET_OFFICERS_FILE}")
        sys.exit(1)

    with open(TARGET_OFFICERS_FILE, "r", encoding="utf-8") as f:
        officers = json.load(f)

    officer_index = build_officer_index(officers)
    total_officers = len(officer_index)
    pad_width = len(str(total_officers))      # 決定補位寬度，例如 4 位 → "0007"

    print(f"📋 target_officers.json 共有 {len(officers)} 筆，"
          f"其中真實官員 {total_officers} 位，編號補位寬度：{pad_width} 位數\n")

    # 掃描 downloads_priso/
    if not os.path.isdir(PRISO_DOWNLOAD_DIR):
        print(f"❌ 找不到下載目錄：{PRISO_DOWNLOAD_DIR}")
        sys.exit(1)

    # 符合「姓名_財產申報_N.pdf」的舊格式
    pattern_old = re.compile(r"^(.+)_財產申報_(\d+)\.pdf$")
    # 符合「NNNN_姓名_財產申報_N.pdf」的已編號格式（跳過）
    pattern_new = re.compile(r"^\d+_(.+)_財產申報_(\d+)\.pdf$")

    renamed = 0
    skipped_already = 0
    skipped_unknown = 0

    files = sorted(os.listdir(PRISO_DOWNLOAD_DIR))
    for fname in files:
        if not fname.endswith(".pdf"):
            continue

        if pattern_new.match(fname):
            skipped_already += 1
            continue           # 已有編號，跳過

        m = pattern_old.match(fname)
        if not m:
            continue           # 不符合預期格式

        name      = m.group(1)
        period    = m.group(2)

        if name not in officer_index:
            print(f"  ⚠️  找不到對應編號：{fname}  (姓名={name})")
            skipped_unknown += 1
            continue

        num       = officer_index[name]
        num_str   = str(num).zfill(pad_width)
        new_fname = f"{num_str}_{name}_財產申報_{period}.pdf"

        old_path  = os.path.join(PRISO_DOWNLOAD_DIR, fname)
        new_path  = os.path.join(PRISO_DOWNLOAD_DIR, new_fname)

        if dry_run:
            print(f"  [預覽] {fname}  →  {new_fname}")
        else:
            if os.path.exists(new_path) and new_path != old_path:
                print(f"  ⚠️  目標檔名已存在，跳過：{new_fname}")
                skipped_unknown += 1
            else:
                os.rename(old_path, new_path)
                print(f"  ✅ {fname}  →  {new_fname}")
        renamed += 1

    print()
    print("=" * 60)
    if dry_run:
        print(f"  預覽完成：可改名 {renamed} 個檔案")
    else:
        print(f"  改名完成：共改名 {renamed} 個檔案")
    print(f"  已跳過（已有編號）：{skipped_already} 個")
    print(f"  無法對應（找不到姓名）：{skipped_unknown} 個")
    print("=" * 60)
    if dry_run:
        print("\n  ➡️  確認無誤後，加上 --apply 執行實際改名：")
        print("       python rename_priso_pdfs_by_target_order.py --apply")


if __name__ == "__main__":
    main()
