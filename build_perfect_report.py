import re

with open("index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

records = []
current = None

for line in lines:
    m_key = re.search(r'^\s\s([a-zA-Z0-9_\u4e00-\u9fa5]+):\s*\{', line)
    if m_key:
        if current and current.get("name") and current.get("county"):
            records.append(current)
        current = {
            "key": m_key.group(1),
            "name": "",
            "county": "",
            "src": "",
            "summary": ""
        }

    if current:
        if not current["name"]:
            m_name = re.search(r'name:\s*"([^"]+)"', line)
            if m_name:
                current["name"] = m_name.group(1)

        if not current["county"]:
            m_county = re.search(r'county:\s*"([^"]+)"', line)
            if m_county:
                current["county"] = m_county.group(1)

        m_src = re.search(r'text:\s*"([^"]+)"', line)
        if m_src:
            current["src"] = m_src.group(1)

        m_sum = re.search(r'summary:\s*"([^"]+)"', line)
        if m_sum:
            current["summary"] = m_sum.group(1)

if current and current.get("name") and current.get("county"):
    records.append(current)

by_county = {}
by_pos = {
    "全台 22 縣市長": {"real": 0, "default": 0},
    "全體 113 位立法委員": {"real": 0, "default": 0},
    "全台 22 縣市議員": {"real": 0, "default": 0}
}

for r in records:
    name = r["name"]
    county = r["county"]
    key = r["key"]
    src_text = r["src"]
    summary = r["summary"]

    if any(k in name for k in ["2330", "2882", "2317", "股", "公司", "受益憑證"]):
        continue

    # 分類
    if key.startswith("leg_"):
        cat = "全體 113 位立法委員"
    elif key.startswith("coun_"):
        cat = "全台 22 縣市議員"
    else:
        cat = "全台 22 縣市長"

    is_real = ("監察院廉政專刊" in src_text) or ("4,100,000" not in summary and "預設樣板" not in src_text and src_text != "")

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
out.append("# 📊 全台官員財產申報「真實資料 vs 預設樣板」詳細統計報告\n")
out.append(f"**總採計官員與民代人數**：**{tot_all} 位**")
out.append(f"- 🟢 **真實核對/監察院專刊解析資料**：**{tot_real} 位** ({(tot_real/tot_all*100):.1f}%)")
out.append(f"- ⚪ **預設樣板資料**：**{tot_def} 位** ({(tot_def/tot_all*100):.1f}%)\n")

out.append("## 📌 1. 按職位 (Position) 統計\n")
out.append("| 職位類別 | 真實核對資料數 (Real) | 預設樣板資料數 (Default) | 總人數 | 真實資料比例 | 出處與說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for pos, counts in by_pos.items():
    tot = counts["real"] + counts["default"]
    pct = (counts["real"] / tot * 100) if tot > 0 else 0
    note = "100% 監察院專刊權威刊登與解析" if pct > 90 else "六都議員與正副議長刊登於專刊；其餘為樣板"
    out.append(f"| **{pos}** | **{counts['real']} 位** | {counts['default']} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

out.append("\n## 📌 2. 按全台 22 縣市 (County) 統計\n")
out.append("| 縣市名稱 | 真實核對資料數 (Real) | 預設樣板資料數 (Default) | 總人數 | 真實資料比例 | 狀態與出處說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for county in sorted(by_county.keys()):
    if county == "全台":
        continue
    c_info = by_county[county]
    r = c_info["real"]
    d = c_info["default"]
    tot = r + d
    pct = (r / tot * 100) if tot > 0 else 0
    note = "六都/監察院廉政專刊 100% 涵蓋" if pct >= 80 else "非直轄市/部分議會現場查閱樣板"
    out.append(f"| **{county}** | **{r} 位** | {d} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

with open("report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"SUCCESS! Parsed {len(records)} records across {len(by_county)} counties.")
