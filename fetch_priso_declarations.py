import os
import sys
import json
import urllib.parse
import re

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

TARGET_OFFICERS_FILE = "target_officers.json"
OUTPUT_PRISO_INDEX = "priso_declarations_index.json"
PRISO_BASE_SEARCH = "https://priso.cy.gov.tw/layout/baselist"

def build_priso_officer_indices():
    if not os.path.exists(TARGET_OFFICERS_FILE):
        print(f"❌ 找不到目標官員名冊：{TARGET_OFFICERS_FILE}")
        return

    with open(TARGET_OFFICERS_FILE, "r", encoding="utf-8") as f:
        officers = json.load(f)

    print("==========================================================")
    print(f" 🔍 監察院 PRISO 系統全台官員/議員財產申報索引建置器")
    print(f" 👥 目標對象：{len(officers)} 位全台縣市長、立委與 22 縣市議員名冊")
    print("==========================================================")

    priso_index = {}

    for idx, o in enumerate(officers, 1):
        name = o.get("name", "")
        county = o.get("county", "")
        position = o.get("position", "")
        key = o.get("key", f"officer_{name}")

        if not name or any(k in name for k in ["2330", "2882", "2317", "股", "公司"]):
            continue

        # 生成 PRISO 官方查詢連結與檢索標記
        encoded_name = urllib.parse.quote(name)
        search_link = f"{PRISO_BASE_SEARCH}?name={encoded_name}"

        # 決定權威層級標籤與來源
        if "市長" in position or "縣長" in position:
            filing_type = "監察院定期申報（全台縣市長）"
            authority = "監察院廉政專刊"
        elif "立委" in position or "立法委員" in position or key.startswith("leg_"):
            filing_type = "監察院定期申報（第11屆立法委員）"
            authority = "監察院廉政專刊"
        elif any(c in county for c in ["臺北", "台北", "新北", "桃園", "臺中", "台中", "臺南", "台南", "高雄"]):
            filing_type = "監察院定期申報（直轄市議員及正副議長）"
            authority = "監察院廉政專刊"
        else:
            filing_type = "縣市議會政風室現場查閱/中選會候選人申報專區"
            authority = "縣市議會政風室現場查閱專區"

        priso_index[name] = {
            "key": key,
            "name": name,
            "county": county,
            "position": position,
            "priso_search_url": search_link,
            "filing_authority": authority,
            "filing_type": filing_type,
            "status": "INDEXED"
        }

    with open(OUTPUT_PRISO_INDEX, "w", encoding="utf-8") as f:
        json.dump(priso_index, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 [成功] 已產出 {len(priso_index)} 位官員/議員之 PRISO 官方檢索索引至 【{OUTPUT_PRISO_INDEX}】！")

if __name__ == "__main__":
    build_priso_officer_indices()
