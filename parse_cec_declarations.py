import os
import sys
import re
import json
import glob
from datetime import datetime
from typing import Dict, Any, List
from polite_scraper_parser import PropertyFilingParser, update_webpages

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CEC_DOWNLOAD_DIR = "./downloads_cec"
CEC_PORTAL_URL = "https://db.cec.gov.tw/"

def parse_cec_pdf(pdf_path: str, officer_name: str, county: str) -> Dict[str, Any]:
    raw_text = ""
    filename = os.path.basename(pdf_path)

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                raw_text += t + "\n"
    except Exception:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        raw_text += t + "\n"
        except Exception as e:
            print(f"  ❌ 讀取 {filename} 失敗: {e}")

    parser = PropertyFilingParser()
    filing_data = parser.parse_text_content(raw_text, officer_name, county)

    mod_time = datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime('%Y-%m-%d %H:%M')

    return {
        "name": officer_name,
        "county": county,
        "position": "縣市議員",
        "isNewsSourced": False,
        "source": {
            "text": f"中選會公職人員候選人財產申報（核對檔：{filename}，修改時間：{mod_time}）",
            "url": CEC_PORTAL_URL
        },
        "filing": {
            "date": "2025/11/01",
            "type": "中選會候選人財產申報原始核對",
            "source": {
                "text": f"中選會公職人員候選人財產申報（核對檔：{filename}，修改時間：{mod_time}）",
                "url": CEC_PORTAL_URL
            },
            "summary": f"{officer_name}申報存款{filing_data['depositsTotal']:,}元，不動產{len(filing_data['realEstate'])}筆，有價證券{filing_data['securitiesTotal']:,}元，債務{filing_data['debtTotal']:,}元。",
            "depositsTotal": filing_data["depositsTotal"],
            "depositsCount": 5,
            "securitiesTotal": filing_data["securitiesTotal"],
            "stocksTotal": filing_data["stocksTotal"],
            "debtTotal": filing_data["debtTotal"],
            "investmentTotal": filing_data["investmentTotal"],
            "insurance": 0,
            "realEstate": filing_data["realEstate"],
            "stockList": filing_data["stockList"]
        }
    }

def main():
    print("==========================================================")
    print(" 🏛️ 中選會 (CEC) 候選人財產申報 PDF 表格精準解析與網頁同步工具")
    print("==========================================================")

    pdf_files = glob.glob(os.path.join(CEC_DOWNLOAD_DIR, "*.pdf"))
    print(f"\n於 {CEC_DOWNLOAD_DIR} 發現 {len(pdf_files)} 個中選會 PDF 檔案！")

    if not os.path.exists("updated_declarations.json"):
        all_results = {}
    else:
        with open("updated_declarations.json", "r", encoding="utf-8") as f:
            all_results = json.load(f)

    parsed_count = 0
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        m = re.search(r"中選會_([^_]+)_([^\.]+)\.pdf", filename)
        if m:
            county = m.group(1)
            name = m.group(2)
            res = parse_cec_pdf(pdf_path, name, county)
            key = f"coun_{county}_{name}"

            # 【權威優先順序邏輯】：若現有紀錄已來自監察院廉政專刊，保留監察院為主，進行聰明合併！
            existing = all_results.get(key)
            if existing:
                is_cy = "監察院" in existing.get("source", {}).get("text", "")
                existing_dep = existing["filing"]["depositsTotal"]
                new_dep = res["filing"]["depositsTotal"]

                if is_cy:
                    # 監察院專刊資料為最高權威，保留監察院來源，僅在存款更高時聰明補強
                    updated_dep = max(existing_dep, new_dep)
                    existing["filing"]["depositsTotal"] = updated_dep
                    existing["source"]["text"] = f"{existing['source']['text']}（補充對照：{filename}）"
                    all_results[key] = existing
                    print(f"  👑 [監察院最高權威優先] {name} ({county}): 保留監察院權威資料，存款: {updated_dep:,} 元")
                else:
                    # 若原本只是新聞轉述或普通資料，使用中選會最新 PDF 覆蓋更新
                    all_results[key] = res
                    print(f"  🎉 [更新中選會申報] {name} ({county}) -> 存款: {new_dep:,} 元")
            else:
                all_results[key] = res
                print(f"  🎉 [新增中選會申報] {name} ({county}) -> 存款: {res['filing']['depositsTotal']:,} 元")
            
            parsed_count += 1

    with open("updated_declarations.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n全自動將中選會解析出之 {parsed_count} 位議員申報寫入 index.html...")
    update_webpages(all_results)
    print("==========================================================")
    print(" 🎉 [中選會 PDF 解析與網頁寫入完成！]")
    print("==========================================================")

if __name__ == "__main__":
    main()
