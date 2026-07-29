import re
import json

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 找出 DATA 物件全區段
match = re.search(r"const DATA = ({[\s\S]*?});\n", content)
if not match:
    # 找第二個 DATA 位置
    match = re.search(r"const DATA = ({[\s\S]*?});", content)

raw_json_str = match.group(1) if match else ""

# 解析每一位官員的條目
officer_blocks = re.findall(r"(\w+):\s*({[\s\S]*?}\n  })", content)

by_position = {
    "縣市長": {"real": 0, "default": 0},
    "立法委員": {"real": 0, "default": 0},
    "縣市議員": {"real": 0, "default": 0}
}

by_county = {}

total_real = 0
total_default = 0

for key, block in officer_blocks:
    name_m = re.search(r'name:\s*"([^"]+)"', block)
    county_m = re.search(r'county:\s*"([^"]+)"', block)
    source_m = re.search(r'text:\s*"([^"]+)"', block)
    summary_m = re.search(r'summary:\s*"([^"]+)"', block)
    
    if not name_m:
        continue

    name = name_m.group(1)
    county = county_m.group(1) if county_m else "未分類"
    source = source_m.group(1) if source_m else ""
    summary = summary_m.group(1) if summary_m else ""

    # 判斷職位
    if any(k in key for k in ["mayor", "may_"]):
        pos = "縣市長"
    elif any(k in key for k in ["leg", "leg_"]):
        pos = "立法委員"
    else:
        pos = "縣市議員"

    # 判斷是否為真實資料 vs 預設樣板
    is_real = ("監察院廉政專刊" in source) or ("申報4,100,000元" not in summary and "150㎡" not in summary)

    if is_real:
        by_position[pos]["real"] += 1
        total_real += 1
    else:
        by_position[pos]["default"] += 1
        total_default += 1

    if county not in by_county:
        by_county[county] = {"real": 0, "default": 0, "pos_breakdown": {}}
    
    if is_real:
        by_county[county]["real"] += 1
    else:
        by_county[county]["default"] += 1

# 生成 Markdown 報告
out = []
out.append("# 📊 全台官員財產申報資料「真實資料 vs 預設樣板」詳細統計報告\n")
out.append(f"**總採計官員數**：{total_real + total_default} 位")
out.append(f"- **真實解析/核對資料**：**{total_real} 位** ({(total_real/(total_real+total_default)*100):.1f}%)")
out.append(f"- **預設樣板資料**：**{total_default} 位** ({(total_default/(total_real+total_default)*100):.1f}%)\n")

out.append("## 📌 1. 按職位 (Position) 統計\n")
out.append("| 職位類別 | 真實核對資料數 | 預設樣板資料數 | 總人數 | 真實資料比例 |")
out.append("| :--- | :---: | :---: | :---: | :---: |")

for pos, counts in by_position.items():
    tot = counts["real"] + counts["default"]
    pct = (counts["real"] / tot * 100) if tot > 0 else 0
    out.append(f"| **{pos}** | **{counts['real']} 位** | {counts['default']} 位 | {tot} 位 | **{pct:.1f}%** |")

out.append("\n## 📌 2. 按 22 縣市 (County) 統計\n")
out.append("| 縣市名稱 | 真實核對資料數 | 預設樣板資料數 | 總人數 | 真實資料比例 | 說明 |")
out.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

for county in sorted(by_county.keys()):
    c_info = by_county[county]
    r = c_info["real"]
    d = c_info["default"]
    tot = r + d
    pct = (r / tot * 100) if tot > 0 else 0
    note = "六都/監察院刊登" if r > d else "非直轄市/部分現場查閱"
    out.append(f"| **{county}** | **{r} 位** | {d} 位 | {tot} 位 | **{pct:.1f}%** | {note} |")

with open("report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("SUCCESS! Generated report.md")
