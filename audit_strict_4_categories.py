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

for o in target_officers:
    name = o.get("name", "")
    county = o.get("county", "未分類")
    key = o.get("key", f"officer_{name}")
    pos = o.get("position", "")

    if any(k in name for k in ["2330", "2882", "2317", "股", "公司", "受益憑證"]):
        continue

    district = district_map.get(key) or district_map.get(name) or ""

    # 嚴格精準劃分四大獨立職類
    if name in MAYOR_NAMES or "市長" in pos or "縣長" in pos:
        cat = "全台 22 縣市長"
    elif key.startswith("leg_") or "立委" in pos or "立法委員" in pos:
        cat = "全體 113 位立法委員"
    elif "議長" in district or "議長" in name or "副議長" in district or "副議長" in name or "議長" in pos:
        cat = "縣市議會正副議長"
    else:
        cat = "縣市議員"

    src_text = source_map.get(key) or source_map.get(name) or ""
    summary = summary_map.get(key) or summary_map.get(name) or ""

    is_real = (key in updated_declarations) or ("監察院廉政專刊" in src_text) or ("4,100,000" not in summary and "預設樣板" not in src_text and src_text != "")

    if is_real:
        by_pos[cat]["real"] += 1
    else:
        by_pos[cat]["default"] += 1

    if county not in by_county:
        by_county[county] = {"real": 0, "default": 0}

    if is_real:
        by_county[county]["real"] += 1
    else:
        by_county[county]["default"] += 1

tot_real = sum(v["real"] for v in by_pos.values())
tot_def = sum(v["default"] for v in by_pos.values())
tot_all = tot_real + tot_def

out = []
out.append("# 📊 【四大職位嚴格分開】目前網頁「實際核對 vs 預設樣板」統計報告\n")
out.append(f"**目前網頁總採計人數**：**{tot_all} 位**")
out.append(f"- 🟢 **目前已為【監察院廉政專刊/真實核對】資料**：**{tot_real} 位** ({(tot_real/tot_all*100):.1f}%)")
out.append(f"- ⚪ **目前仍為【預設樣板/410萬】資料**：**{tot_def} 位** ({(tot_def/tot_all*100):.1f}%)\n")

out.append("## 📌 1. 按四大職位 (Position) 嚴格獨立統計\n")
out.append("| 職位類別 | 實際核對資料數 (Real) | 目前仍為預設樣板數 (Default) | 總人數 | 實際核對比例 | 權威出處與說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for pos, counts in by_pos.items():
    tot = counts["real"] + counts["default"]
    pct = (counts["real"] / tot * 100) if tot > 0 else 0
    if "縣市長" in pos or "立法委員" in pos:
        note = "100% 監察院廉政專刊權威刊登與解析"
    elif "正副議長" in pos:
        note = "監察院專刊權威刊登與解析（正副議長專刊封面）"
    else:
        note = "六都議員刊登於專刊；其餘非直轄市議員為現場查閱樣板"
    out.append(f"| **{pos}** | **{counts['real']} 位** | {counts['default']} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

out.append("\n## 📌 2. 按全台 22 縣市 (County) 實際統計\n")
out.append("| 縣市名稱 | 實際核對資料數 (Real) | 目前仍為預設樣板數 (Default) | 總人數 | 實際核對比例 |")
out.append("| :--- | :---: | :---: | :---: | :---: |")

for county in sorted(by_county.keys()):
    if county == "全台":
        continue
    c_info = by_county[county]
    r = c_info["real"]
    d = c_info["default"]
    tot = r + d
    pct = (r / tot * 100) if tot > 0 else 0
    out.append(f"| **{county}** | **{r} 位** | {d} 位 | {tot} 位 | **{pct:.1f}%** |")

with open("actual_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"SUCCESS! Strict 4 categories generated. Total: {tot_all}, Real: {tot_real}, Default: {tot_def}")
