import json
import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

with open("target_officers.json", "r", encoding="utf-8") as f:
    target_officers = json.load(f)

with open("updated_declarations.json", "r", encoding="utf-8") as f:
    updated_declarations = json.load(f)

blocks = re.findall(r'(\w+):\s*\{([\s\S]*?)\n\s*\},?\n', content)

source_map = {}
summary_map = {}
district_map = {}

for key, block in blocks:
    nm = re.search(r'name:\s*"([^"]+)"', block)
    tx = re.search(r'text:\s*"([^"]+)"', block)
    sm = re.search(r'summary:\s*"([^"]+)"', block)
    dt = re.search(r'district:\s*"([^"]+)"', block)

    if nm:
        name = nm.group(1)
        if tx:
            source_map[key] = tx.group(1)
            source_map[name] = tx.group(1)
        if sm:
            summary_map[key] = sm.group(1)
            summary_map[name] = sm.group(1)
        if dt:
            district_map[key] = dt.group(1)
            district_map[name] = dt.group(1)

by_pos = {
    "全台 22 縣市長": {"real": 0, "default": 0},
    "全體 113 位立法委員": {"real": 0, "default": 0},
    "縣市議會正副議長": {"real": 0, "default": 0},
    "縣市議員": {"real": 0, "default": 0}
}

by_county = {}

MAYOR_NAMES = {"侯友宜", "蔣萬安", "張善政", "柯文哲", "盧秀燕", "陳其邁", "黃偉哲", "高虹安", "楊文科", "鍾東錦", "王惠美", "許淑華", "張麗善", "黃敏惠", "翁章梁", "周春米", "林姿妙", "徐榛蔚", "饒慶鈴", "陳光復", "陳福海", "王忠銘", "謝國樑"}

# ── 縣市統計：從 updated_declarations 的 coun_ key 解析縣市 ───────────────────
# target_officers.json 的 county 欄幾乎全是 "全台"，無法區分縣市。
# 改用 updated_declarations 的 key 格式解析：
#   coun_臺北市_11  → 臺北市
#   coun_新北市_42  → 新北市
#   其他 key（縣市長/立委的短英文縮寫）→ 歸入 "全台"，不列入縣市表
def county_from_key(k):
    m = re.match(r'^coun_(.+)_\d+$', k)
    return m.group(1) if m else "全台"

# 預先建立 name → key 對照（供後面職類判斷用）
name_to_key = {v.get("name", ""): k for k, v in updated_declarations.items()}

for o in target_officers:
    name = o.get("name", "")
    pos  = o.get("position", "")

    if any(k in name for k in ["2330", "2882", "2317", "股", "公司", "受益憑證"]):
        continue

    # 從 updated_declarations 找該人對應的 key（比 target_officers.json 的 key 欄更準確）
    key = name_to_key.get(name) or o.get("key", f"officer_{name}")

    district = district_map.get(key) or district_map.get(name) or ""

    # ── 職類判斷 ──────────────────────────────────────────────────────────────
    # 縣市長：姓名在白名單中
    # 立法委員：key 不是 coun_ 開頭、且不在 MAYOR_NAMES
    #   → updated_declarations 裡立委的 key 是短英文縮寫（miaoboya, houyi…）
    #   → 舊判斷 key.startswith("leg_") 完全失效，改用排除法
    # 正副議長：district 或姓名含「議長」
    # 其餘：縣市議員
    if name in MAYOR_NAMES or "市長" in pos or "縣長" in pos:
        cat = "全台 22 縣市長"
    elif not key.startswith("coun_") and name not in MAYOR_NAMES:
        cat = "全體 113 位立法委員"
    elif "議長" in district or "議長" in name or "副議長" in district or "副議長" in name or "議長" in pos:
        cat = "縣市議會正副議長"
    else:
        cat = "縣市議員"
    # ──────────────────────────────────────────────────────────────────────────

    src_text = source_map.get(key) or source_map.get(name) or ""
    summary  = summary_map.get(key) or summary_map.get(name) or ""

    is_real = (
        (key in updated_declarations) or
        ("監察院廉政專刊" in src_text) or
        ("PRISO" in src_text) or
        ("4,100,000" not in summary and "預設樣板" not in src_text and src_text != "")
    )

    if is_real:
        by_pos[cat]["real"] += 1
    else:
        by_pos[cat]["default"] += 1

    # ── 縣市統計：只統計議員（coun_ key），略過縣市長/立委 ────────────────────
    county = county_from_key(key)
    if county != "全台":
        if county not in by_county:
            by_county[county] = {"real": 0, "default": 0}
        if is_real:
            by_county[county]["real"] += 1
        else:
            by_county[county]["default"] += 1
    # ──────────────────────────────────────────────────────────────────────────

tot_real = sum(v["real"] for v in by_pos.values())
tot_def  = sum(v["default"] for v in by_pos.values())
tot_all  = tot_real + tot_def

out = []
out.append("# 📊 【四大職位嚴格獨立劃分】目前網頁「實際核對 vs 預設樣板」統計報告\n")
out.append(f"**目前網頁總採計人數**：**{tot_all} 位**")
out.append(f"- 🟢 **目前已為【監察院廉政專刊/真實核對/PRISO】資料**：**{tot_real} 位** ({(tot_real/tot_all*100):.1f}%)")
out.append(f"- ⚪ **目前仍為【預設樣板/410萬】資料**：**{tot_def} 位** ({(tot_def/tot_all*100):.1f}%)\n")

out.append("## 📌 1. 按四大獨立職位 (Position) 嚴格統計\n")
out.append("| 職位類別 | 實際核對資料數 (Real) | 目前仍為預設樣板數 (Default) | 總人數 | 實際核對比例 | 權威出處與說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for pos, counts in by_pos.items():
    tot = counts["real"] + counts["default"]
    pct = (counts["real"] / tot * 100) if tot > 0 else 0
    if "縣市長" in pos or "立法委員" in pos:
        note = "100% 監察院廉政專刊權威刊登與解析"
    elif "正副議長" in pos:
        note = "監察院專刊權威刊登與解析（正副議長專刊專頁）"
    else:
        note = "六都議員刊登於專刊；其餘非直轄市議員現場查閱 / PRISO 個人 PDF"
    out.append(f"| **{pos}** | **{counts['real']} 位** | {counts['default']} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

out.append("\n## 📌 2. 按全台 22 縣市 (County) 實際統計（僅議員）\n")
out.append("| 縣市名稱 | 實際核對資料數 (Real) | 目前仍為預設樣板數 (Default) | 總人數 | 實際核對比例 |")
out.append("| :--- | :---: | :---: | :---: | :---: |")

for county in sorted(by_county.keys()):
    c_info = by_county[county]
    r   = c_info["real"]
    d   = c_info["default"]
    tot = r + d
    pct = (r / tot * 100) if tot > 0 else 0
    out.append(f"| **{county}** | **{r} 位** | {d} 位 | {tot} 位 | **{pct:.1f}%** |")

with open("actual_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"SUCCESS! Total: {tot_all}, Real: {tot_real}, Default: {tot_def}")
print(f"Counties breakdown: {len(by_county)} 縣市")
