import glob
import pdfplumber
import re
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def parse_amount(val_str: str) -> float:
    if not val_str:
        return 0.0
    cleaned = re.sub(r'[^\d\.]', '', str(val_str))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

pdf_files = sorted(glob.glob("./downloads_priso/*上官秋燕*.pdf"))

for p in pdf_files:
    print(f"\n==========================================")
    print(f"📄 File: {p}")
    with pdfplumber.open(p) as pdf:
        full_text = ""
        stock_list = []
        stocks_total = 0

        for page in pdf.pages:
            t = page.extract_text() or ""
            full_text += t + "\n"

            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                
                # 檢查整張表格是否屬於股票區塊
                table_text = "".join([str(cell).replace(" ", "").replace("\n", "") for row in table for cell in row if cell])
                if ("股票" in table_text or "有價證券" in table_text) and ("股數" in table_text or "票面價額" in table_text or "中鋼" in table_text):
                    for row in table:
                        row_cells = [str(c).strip().replace("\n", "") for c in row if c]
                        row_str = "".join(row_cells).replace(" ", "")

                        if "本欄空白" in row_str or not row_cells or "名稱" in row_str or "票面價額" in row_str or "股票" in row_str:
                            continue

                        stk_name = row_cells[0]
                        stk_owner = row_cells[1] if len(row_cells) > 1 else "上官秋燕"
                        shares_val = int(parse_amount(row_cells[2])) if len(row_cells) > 2 else 0
                        amt_val = int(parse_amount(row_cells[-1])) if len(row_cells) >= 4 else 0

                        if stk_name and not stk_name.isdigit() and len(stk_name) < 25:
                            if not any(k in stk_name for k in ["申報人", "申報日", "服務機關", "職稱", "姓名", "機關"]):
                                if not any(x["name"] == stk_name for x in stock_list):
                                    stock_list.append({
                                        "name": stk_name,
                                        "owner": stk_owner,
                                        "shares": f"{shares_val:,} 股" if shares_val > 0 else "1 股",
                                        "amount": amt_val
                                    })

        m = re.search(r'(?:1\.股票|股票|有價證券)[^\n]*?總(?:價|金)額[：:\s]*(?:新臺幣)?\s*([\d,]+)\s*元', full_text)
        if m:
            stocks_total = int(parse_amount(m.group(1)))

        print(f"  🎯 股票總金額 Header: {stocks_total:,} 元")
        print(f"  🎯 萃取股票明細 ({len(stock_list)} 筆):", stock_list)
