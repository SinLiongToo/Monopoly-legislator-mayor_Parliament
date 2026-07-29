import json
import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

with open("target_officers.json", "r", encoding="utf-8") as f:
    target_officers = json.load(f)

with open("updated_declarations.json", "r", encoding="utf-8") as f:
    updated_declarations = json.load(f)

officer_matches = re.findall(r'name:\s*"([^"]+)"[\s\S]*?text:\s*"([^"]+)"', content)
source_map = dict(officer_matches)

by_position = {
    "全台22縣市長": {"real": 0, "default": 0},
    "113席立法委員": {"real": 0, "default": 0},
    "縣市議員": {"real": 0, "default": 0}
}

by_county = {}

for o in target_officers:
    name = o.get("name", "")
    county = o.get("county", "未分類")
    key = o.get("key", f"officer_{name}")
    pos = o.get("position", "")

    if any(k in name for k in ["2330", "2882", "2317", "股", "公司", "受益憑證"]):
        continue

    if "立委" in pos or "立法委員" in pos or key.startswith("leg_"):
        category = "113席立法委員"
    elif "市長" in pos or "縣長" in pos or key.startswith("may_") or key.startswith("officer_"):
        category = "全台22縣市長"
    else:
        category = "縣市議員"

    src_text = source_map.get(name, "")
    is_real = (key in updated_declarations) or ("監察院" in src_text) or ("中選會" in src_text and "現場查閱專區" not in src_text)

    if is_real:
        by_position[category]["real"] += 1
    else:
        by_position[category]["default"] += 1

    if county not in by_county:
        by_county[county] = {"real": 0, "default": 0}

    if is_real:
        by_county[county]["real"] += 1
    else:
        by_county[county]["default"] += 1

out = []
tot_real = sum(v["real"] for v in by_position.values())
tot_def = sum(v["default"] for v in by_position.values())
tot_all = tot_real + tot_def

out.append("# 📊 全台官員財產申報資料「真實資料 vs 預設樣板」詳細統計報告\n")
out.append(f"**總採計官員與民代人數**：**{tot_all} 位**")
out.append(f"- 🟢 **真實核對/監察院解析資料**：**{tot_real} 位** ({(tot_real/tot_all*100):.1f}%)")
out.append(f"- ⚪ **預設樣板資料**：**{tot_def} 位** ({(tot_def/tot_all*100):.1f}%)\n")

out.append("## 📌 1. 按職位 (Position) 統計\n")
out.append("| 職位類別 | 真實核對資料數 (Real) | 預設樣板資料數 (Default) | 總人數 | 真實資料比例 | 說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for pos, counts in by_position.items():
    tot = counts["real"] + counts["default"]
    pct = (counts["real"] / tot * 100) if tot > 0 else 0
    note = "100% 監察院專刊權威刊登" if pct > 90 else "六都及正副議長刊登於專刊；其餘為樣板"
    out.append(f"| **{pos}** | **{counts['real']} 位** | {counts['default']} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

out.append("\n## 📌 2. 按 22 縣市 (County) 統計\n")
out.append("| 縣市名稱 | 真實核對資料數 (Real) | 預設樣板資料數 (Default) | 總人數 | 真實資料比例 | 說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for county in sorted(by_county.keys()):
    if county == "全台":
        continue
    c_info = by_county[county]
    r = c_info["real"]
    d = c_info["default"]
    tot = r + d
    pct = (r / tot * 100) if tot > 0 else 0
    note = "六都/監察院專刊覆蓋" if pct >= 80 else "非直轄市/部分現場查閱"
    out.append(f"| **{county}** | **{r} 位** | {d} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

with open("report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE!")
