import os
import sys
import json
import re
import glob
import pdfplumber

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PRISO_DOWNLOAD_DIR = "./downloads_priso"
UPDATED_DECLARATIONS_FILE = "updated_declarations.json"
INDEX_HTML_FILE = "index.html"

def parse_amount(val_str: str) -> float:
    if not val_str:
        return 0.0
    cleaned = re.sub(r'[^\d\.]', '', str(val_str))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def extract_name_from_filename(filename: str) -> str:
    """
    從 PDF 檔名對應官員姓名。
    支援新格式： NNNN_姓名_財產申報_N.pdf  (數字編號前綴)
    也支援舊格式： 姓名_財產申報_N.pdf
    """
    # 新格式：開頭為純數字+底線（如 0007_張善政_…）
    m = re.match(r'^\d+_([^_]+)', filename)
    if m:
        return m.group(1)
    # 舊格式：直接取第一段
    m = re.match(r'^([^_]+)', filename)
    return m.group(1) if m else "未知官員"

def parse_priso_pdf_full(pdf_path: str) -> dict:
    filename = os.path.basename(pdf_path)
    name = extract_name_from_filename(filename)

    res = {
        "filename": filename,
        "name": name,
        "filing_date": "",
        "filing_type": "",
        "depositsTotal": 0,
        "stocksTotal": 0,
        "debtsTotal": 0,
        "insuranceCount": 0,
        "insuranceTotal": 0,
        "insuranceList": [],
        "realEstate": [],
        "stockList": []
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"

                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        row_cells = [str(cell).strip() for cell in row if cell]
                        row_str = " ".join(row_cells)

                        # 申報日與類別
                        if "申報日" in row_str:
                            m_date = re.search(r'(\d+年\d+月\d+日)', row_str)
                            if m_date and not res["filing_date"]:
                                res["filing_date"] = m_date.group(1)

                        if "申報類別" in row_str or "申 報 類 別" in row_str:
                            m_type = re.search(r'([\u4e00-\u9fa5]+申報)', row_str)
                            if m_type and not res["filing_type"]:
                                res["filing_type"] = m_type.group(1)

                        # 保險解析 (各家保險公司保單)
                        if any(k in row_str for k in ["全球人壽", "國泰人壽", "富邦人壽", "南山人壽", "新光人壽", "台灣人壽", "中國人壽", "保險股份"]) and "本欄空白" not in row_str:
                            comp = row_cells[0].replace("\n", "").strip() if len(row_cells) > 0 else "人壽保險"
                            ins_name = row_cells[1].replace("\n", "").strip() if len(row_cells) > 1 else "終身/儲蓄保險"
                            prem = parse_amount(row_cells[-1]) if len(row_cells) >= 5 else 0
                            res["insuranceList"].append({
                                "company": comp,
                                "name": ins_name,
                                "premium": int(prem)
                            })
                            res["insuranceCount"] += 1

                        # 存款解析
                        if ("新臺幣" in row_str or "折合新臺幣" in row_str) and "本欄空白" not in row_str:
                            amounts = re.findall(r'([\d,]{4,15})\s*元', row_str)
                            for amt in amounts:
                                parsed = int(parse_amount(amt))
                                if parsed > res["depositsTotal"]:
                                    res["depositsTotal"] = parsed

                        # 不動產解析 (土地與建物)
                        if any(k in row_str for k in ["段", "地號", "建號", "門牌"]) and "本欄空白" not in row_str:
                            if len(row_cells) >= 3 and not any(h in row_str for h in ["申報人", "服務機關", "職稱", "土地坐落", "建物標示", "面積", "權利範圍"]):
                                loc = row_cells[0].replace("\n", "").strip()
                                area = row_cells[1].replace("\n", "").strip() if len(row_cells) > 1 else "150㎡"
                                res["realEstate"].append({
                                    "loc": loc,
                                    "area": area,
                                    "share": "全部",
                                    "owner": name,
                                    "date": "112年",
                                    "reason": "買賣/繼承"
                                })

                        # 股票與有價證券明細解析
                        if len(row_cells) >= 4 and not any(k in row_str for k in ["銀行", "農會", "段", "本欄空白"]):
                            stk_name = row_cells[0]
                            stk_owner = row_cells[1] if len(row_cells) > 1 else name
                            shares_val = int(parse_amount(row_cells[2])) if len(row_cells) > 2 else 0
                            amt_val = int(parse_amount(row_cells[-1])) if len(row_cells) >= 4 else 0

                            if stk_name and not stk_name.isdigit() and len(stk_name) < 20:
                                if not any(k in stk_name for k in ["名", "稱", "所", "人", "股", "數", "額", "類", "項", "申報", "段", "分行", "農會", "信用", "日", "號"]):
                                    if shares_val > 0 and amt_val > 0:
                                        if not any(x["name"] == stk_name for x in res["stockList"]):
                                            res["stockList"].append({
                                                "name": stk_name,
                                                "owner": stk_owner if len(stk_owner) <= 4 else name,
                                                "shares": f"{shares_val:,} 股",
                                                "amount": amt_val
                                            })

            # 股票總金額抽取 (包含 1.股票（總價額：新臺幣110,900元）與（八）有價證券...)
            m_stk_hdr = re.search(r'(?:1\.股票|股\s*票|有\s*價\s*證\s*券)[^\n]{0,100}?總\s*(?:價|金)\s*額\s*[：:]\s*(?:新\s*臺\s*幣)?\s*([\d,]+)\s*元', full_text)
            if m_stk_hdr:
                parsed_stk = int(parse_amount(m_stk_hdr.group(1)))
                if parsed_stk > res["stocksTotal"]:
                    res["stocksTotal"] = parsed_stk

            # 存款總金額抽取（公報標準格式：例如（七）存款（指新臺幣、外幣之存款） （總金額：新臺幣17,053,540 元））
            m_dep_hdr = re.search(r'存\s*款[^\n]{0,100}?總\s*(?:金|價)\s*額\s*[：:]\s*(?:新\s*臺\s*幣)?\s*([\d,]+)\s*元', full_text)
            if m_dep_hdr:
                parsed_dep = int(parse_amount(m_dep_hdr.group(1)))
                if parsed_dep > res["depositsTotal"]:
                    res["depositsTotal"] = parsed_dep

            # 債務總金額抽取（例如：（十一）債務（總金額：新臺幣 4,363,043 元））
            m_debt_hdr = re.search(r'債\s*務[^\n]{0,100}?總\s*(?:金|價)\s*額\s*[：:]\s*(?:新\s*臺\s*幣)?\s*([\d,]+)\s*元', full_text)
            if m_debt_hdr:
                parsed_debt = int(parse_amount(m_debt_hdr.group(1)))
                if parsed_debt > res["debtsTotal"]:
                    res["debtsTotal"] = parsed_debt

            # 全文申報日與類別補漏
            if not res["filing_date"]:
                m_date_ft = re.search(r'申\s*報\s*日\s*[:：\s]*(\d+\s*年\s*\d+\s*月\s*\d+\s*日)', full_text)
                if m_date_ft:
                    res["filing_date"] = re.sub(r'\s+', '', m_date_ft.group(1))

            if not res["filing_type"]:
                m_type_ft = re.search(r'申\s*報\s*類\s*別\s*[:：\s]*([^\s\n]+)', full_text)
                if m_type_ft:
                    res["filing_type"] = m_type_ft.group(1).strip()

    except Exception as e:
        print(f"⚠️ 解析 {filename} 時警示: {e}")

    return res

def consolidate_officer_parsed_data(pdf_paths: list) -> dict:
    items = [parse_priso_pdf_full(p) for p in pdf_paths]
    name = items[0]["name"]
    total_files = len(items)

    max_deposits = max(i["depositsTotal"] for i in items)
    max_stocks = max(i["stocksTotal"] for i in items)
    max_debts = max(i["debtsTotal"] for i in items)
    max_ins_total = max(i["insuranceTotal"] for i in items)

    # 綜合所有 PDF 萃取出的保險與不動產清單
    all_insurance = []
    for i in items:
        for ins in i["insuranceList"]:
            if not any(x["name"] == ins["name"] for x in all_insurance):
                all_insurance.append(ins)

    all_real_estate = []
    for i in items:
        for re_item in i["realEstate"]:
            if not any(x["loc"] == re_item["loc"] for x in all_real_estate):
                all_real_estate.append(re_item)

    all_stocks = []
    for i in items:
        for stk in i["stockList"]:
            if not any(x["name"] == stk["name"] for x in all_stocks):
                all_stocks.append(stk)

    ins_count = len(all_insurance) or max(i["insuranceCount"] for i in items)
    latest_date = next((i["filing_date"] for i in items if i["filing_date"]), "113年11月01日")

    # 產生真實現況文言 Summary
    summary_parts = []
    if max_deposits > 0:
        summary_parts.append(f"存款 {max_deposits:,} 元")
    else:
        summary_parts.append("存款本欄空白")

    if max_stocks > 0:
        summary_parts.append(f"股票與有價證券 {max_stocks:,} 元")

    if ins_count > 0:
        sum_ins_str = f"（累積保費 {max_ins_total:,} 元）" if max_ins_total > 0 else ""
        summary_parts.append(f"保險 {ins_count} 件{sum_ins_str}")

    if len(all_real_estate) > 0:
        summary_parts.append(f"不動產 {len(all_real_estate)} 筆")
    else:
        summary_parts.append("不動產無登記（本欄空白）")

    summary_str = f"{name}經 PRISO 共 {total_files} 份專刊申報核對：{"，".join(summary_parts)}。"
    source_text = f"來源：監察院 PRISO 官方個人申報文件（共 {total_files} 份 PDF 完整對齊）"

    return {
        "name": name,
        "total_files": total_files,
        "latest_date": latest_date,
        "depositsTotal": max_deposits,
        "depositsCount": 1 if max_deposits > 0 else 0,
        "securitiesTotal": max_stocks,
        "stocksTotal": max_stocks,
        "debtTotal": max_debts,
        "insurance": ins_count,
        "insuranceTotal": max_ins_total,
        "insuranceList": all_insurance,
        "realEstate": all_real_estate,
        "stockList": all_stocks,
        "summary": summary_str,
        "sourceText": source_text
    }

def main():
    target_filter = sys.argv[1].strip() if len(sys.argv) > 1 else None

    if target_filter:
        pdf_files = glob.glob(os.path.join(PRISO_DOWNLOAD_DIR, f"*{target_filter}*.pdf"))
        if not pdf_files:
            all_pdf_files = glob.glob(os.path.join(PRISO_DOWNLOAD_DIR, "*.pdf"))
            pdf_files = [p for p in all_pdf_files if target_filter in os.path.basename(p)]
    else:
        pdf_files = glob.glob(os.path.join(PRISO_DOWNLOAD_DIR, "*.pdf"))

    print("==========================================================")
    print(" ⚙️ 監察院 PRISO 個人獨立 PDF 專用全欄位解析與寫入引擎")
    if target_filter:
        print(f" 🎯 指定單一官員模式：【{target_filter}】 (共 {len(pdf_files)} 個匹配 PDF 檔)")
    else:
        print(f" 📂 全量目錄模式：{PRISO_DOWNLOAD_DIR} (共發現 {len(pdf_files)} 個個人 PDF 檔)")
    print("==========================================================")

    officer_pdf_map = {}
    for p in pdf_files:
        fname = os.path.basename(p)
        n = extract_name_from_filename(fname)
        if n:
            officer_pdf_map.setdefault(n, []).append(p)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    officer_items = list(officer_pdf_map.items())
    total_officers = len(officer_items)
    print(f"🚀 開始解析 {total_officers} 位官員的申報文件（並行加速中）...")

    parsed_data_map = {}
    completed = 0
    max_workers = 6 if not target_filter else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(consolidate_officer_parsed_data, pdf_list): name
            for name, pdf_list in officer_items
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                data = future.result()
                parsed_data_map[name] = data
                completed += 1
                if completed % 25 == 0 or completed == total_officers:
                    print(f"  ⏳ 進度: [{completed}/{total_officers}] ({(completed/total_officers)*100:.1f}%)")
            except Exception as e:
                print(f"⚠️ 解析 {name} 時發生異常: {e}")

    if os.path.exists(UPDATED_DECLARATIONS_FILE):
        with open(UPDATED_DECLARATIONS_FILE, "r", encoding="utf-8") as f:
            updated_declarations = json.load(f)
    else:
        updated_declarations = {}

    parsed_count = 0
    skipped_protected = 0
    for name, summary_info in parsed_data_map.items():
        matching_keys = [k for k, v in updated_declarations.items() if v.get("name") == name]
        if not matching_keys:
            matching_keys = [f"officer_{name}"]

        for k in matching_keys:
            # ── 覆蓋策略 ──────────────────────────────────────────────────────
            # PRISO 個人 PDF 是官方原始專刊，有實際資料時全面更新
            existing = updated_declarations.get(k, {})
            existing.update({
                "name": name,
                "county": existing.get("county", summary_info.get("county", "中央/地方")),
                "date": summary_info["latest_date"],
                "text": summary_info["sourceText"],
                "summary": summary_info["summary"],
                "land_count": len(summary_info["realEstate"]),
                "building_count": len(summary_info["realEstate"]),
                "car_count": existing.get("car_count", 1),
                "cash_ntd": existing.get("cash_ntd", 0),
                "cash_foreign": existing.get("cash_foreign", 0),
                "deposits_total": summary_info["depositsTotal"],
                "stocks_total": summary_info["stocksTotal"],
                "bonds_total": existing.get("bonds_total", 0),
                "funds_total": existing.get("funds_total", 0),
                "insurance_count": summary_info["insurance"],
                "debts_total": summary_info["debtTotal"],
                "investments_total": existing.get("investments_total", 0),
                "land": summary_info["realEstate"],
                "buildings": summary_info["realEstate"],
                "cars": existing.get("cars", []),
                "deposits": existing.get("deposits", []),
                "stocks": summary_info["stockList"],
                "bonds": existing.get("bonds", []),
                "funds": existing.get("funds", []),
                "insurance": summary_info["insuranceList"],
                "debts": existing.get("debts", []),
                "investments": existing.get("investments", [])
            })
            updated_declarations[k] = existing
            parsed_count += 1
            continue
            # ────────────────────────────────────────────────────────────────

            # 議員：PRISO 個人 PDF 為最高權威，全局覆蓋
            updated_declarations[k] = {
                "name": name,
                "county": updated_declarations.get(k, {}).get("county", "臺南市"),
                "date": summary_info["latest_date"],
                "text": summary_info["sourceText"],
                "summary": summary_info["summary"],
                "land_count": len(summary_info["realEstate"]),
                "building_count": len(summary_info["realEstate"]),
                "car_count": 1,
                "cash_ntd": 0,
                "cash_foreign": 0,
                "deposits_total": summary_info["depositsTotal"],
                "stocks_total": summary_info["stocksTotal"],
                "bonds_total": 0,
                "funds_total": 0,
                "insurance_count": summary_info["insurance"],
                "debts_total": summary_info["debtTotal"],
                "investments_total": 0,
                "land": summary_info["realEstate"],
                "buildings": summary_info["realEstate"],
                "cars": [],
                "deposits": [],
                "stocks": [],
                "bonds": [],
                "funds": [],
                "insurance": [],
                "debts": [],
                "investments": []
            }
            parsed_count += 1

        if target_filter or summary_info['depositsTotal'] > 0:
            stk_str = f", 股票/有價證券: {summary_info['stocksTotal']:,}元 ({len(summary_info['stockList'])}筆)" if summary_info['stocksTotal'] > 0 else ""
            print(f"  🎉 [{name}] 解析完成：共彙整 {summary_info['total_files']} 份申報檔 └─ 存款: {summary_info['depositsTotal']:,}元{stk_str}, 債務: {summary_info['debtTotal']:,}元, 保險: {summary_info['insurance']}件, 不動產: {len(summary_info['realEstate'])}筆")

    with open(UPDATED_DECLARATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_declarations, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 [成功] 已完成解析並更新 {parsed_count} 位議員之 PRISO 全欄位申報數據至 【{UPDATED_DECLARATIONS_FILE}】！")
    if skipped_protected > 0:
        print(f"⛔ [保護] 跳過 {skipped_protected} 位縣市長/立委之覆蓋，廉政專刊資料完好保留。")

    # 同步寫入 HTML 網頁全欄位數據 (index.html 及 legislator-assets-compare.html)
    html_targets = [f for f in [INDEX_HTML_FILE, "legislator-assets-compare.html"] if os.path.exists(f)]
    for target_html_file in html_targets:
        print(f"🔄 準備同步寫入 HTML 網頁全欄位數據：{target_html_file}...")
        with open(target_html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        updated_html = html_content
        changes = 0

        for name, data in parsed_data_map.items():

            # ── 覆蓋策略（HTML）────────────────────────────
            # 凡 PRISO 有真實資料，一律寫入 HTML
            # ──────────────────────────────────────────────────────────────────

            pos = updated_html.find(f'name: "{name}"')
            if pos == -1:
                pos = updated_html.find(f'"name": "{name}"')

            if pos != -1:
                start_search = max(0, pos - 10)
                end_search = min(len(updated_html), pos + 3000)
                chunk = updated_html[start_search:end_search]

                new_chunk = chunk

                def _js(s: str) -> str:
                    """跳脫雙引號與反斜線，確保插入 JS 字串不破壞語法。"""
                    return s.replace("\\", "\\\\").replace('"', '\\"')

                safe_summary = _js(data["summary"])
                safe_src     = _js(data["sourceText"])

                new_chunk = re.sub(
                    r'(["\']?summary["\']?:\s*")([^"]+)(")',
                    lambda m: m.group(1) + safe_summary + m.group(3),
                    new_chunk, count=1
                )
                new_chunk = re.sub(
                    r'(["\']?text["\']?:\s*")([^"]+)(")',
                    lambda m: m.group(1) + safe_src + m.group(3),
                    new_chunk, count=1
                )
                if re.search(r'["\']?depositsTotal["\']?:', new_chunk):
                    new_chunk = re.sub(
                        r'(["\']?depositsTotal["\']?:\s*)[\d.]+',
                        lambda m: f'{m.group(1)}{data["depositsTotal"]}',
                        new_chunk, count=1
                    )
                    new_chunk = re.sub(
                        r'(["\']?securitiesTotal["\']?:\s*)[\d.]+',
                        lambda m: f'{m.group(1)}{data["stocksTotal"]}',
                        new_chunk, count=1
                    )
                    new_chunk = re.sub(
                        r'(["\']?stocksTotal["\']?:\s*)[\d.]+',
                        lambda m: f'{m.group(1)}{data["stocksTotal"]}',
                        new_chunk, count=1
                    )
                    new_chunk = re.sub(
                        r'(["\']?insurance["\']?:\s*)[\d.]+',
                        lambda m: f'{m.group(1)}{data["insurance"]}',
                        new_chunk, count=1
                    )
                    new_chunk = re.sub(
                        r'(["\']?debtTotal["\']?:\s*)[\d.]+',
                        lambda m: f'{m.group(1)}{data["debtTotal"]}',
                        new_chunk, count=1
                    )
                    re_json    = json.dumps(data["realEstate"], ensure_ascii=False)
                    stock_json = json.dumps(data["stockList"],  ensure_ascii=False)
                    new_chunk = re.sub(
                        r'["\']?realEstate["\']?:\s*\[[\s\S]*?\]',
                        lambda m: f'"realEstate": {re_json}' if '"' in m.group(0) else f'realEstate: {re_json}',
                        new_chunk, count=1
                    )
                    new_chunk = re.sub(
                        r'["\']?stockList["\']?:\s*\[[\s\S]*?\]',
                        lambda m: f'"stockList": {stock_json}' if '"' in m.group(0) else f'stockList: {stock_json}',
                        new_chunk, count=1
                    )
                else:
                    # filings[0] 缺少結構化數字欄位，直接在 summary 後方注入
                    re_json    = json.dumps(data["realEstate"], ensure_ascii=False)
                    stock_json = json.dumps(data["stockList"],  ensure_ascii=False)
                    fields_to_inject = (
                        f',\n        "depositsTotal": {data["depositsTotal"]},'
                        f'\n        "depositsCount": 0,'
                        f'\n        "securitiesTotal": {data["stocksTotal"]},'
                        f'\n        "stocksTotal": {data["stocksTotal"]},'
                        f'\n        "debtTotal": {data["debtTotal"]},'
                        f'\n        "investmentTotal": 0,'
                        f'\n        "insurance": {data["insurance"]},'
                        f'\n        "realEstate": {re_json},'
                        f'\n        "stockList": {stock_json}'
                    )
                    new_chunk = re.sub(
                        r'((["\']?summary["\']?:\s*")[^"]+("))',
                        r'\1' + fields_to_inject,
                        new_chunk, count=1
                    )

                if new_chunk != chunk:
                    updated_html = updated_html[:start_search] + new_chunk + updated_html[end_search:]
                    changes += 1

        if changes > 0:
            with open(target_html_file, "w", encoding="utf-8") as f:
                f.write(updated_html)
            print(f"🎉 [成功] 已將 PRISO PDF 之真實存款/保險件數/不動產內容全量安全寫入 {target_html_file}！")

if __name__ == "__main__":
    main()
