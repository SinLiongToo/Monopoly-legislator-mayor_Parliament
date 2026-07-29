import glob
import pdfplumber
import re
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pdf_files = sorted(glob.glob("./downloads_priso/*上官秋燕*.pdf"))
print(f"📂 找到上官秋燕的 PDF 檔案共 {len(pdf_files)} 個：\n")

for p in pdf_files:
    print(f"==========================================")
    print(f"📄 File: {p}")
    with pdfplumber.open(p) as pdf:
        full_text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            t = page.extract_text() or ""
            full_text += t + "\n"
            
            if "股票" in t or "證券" in t or "股" in t:
                print(f"--- Page {page_num} Stock Text ---")
                lines = [line.strip() for line in t.splitlines() if any(k in line for k in ["股票", "證券", "股", "金額", "所有人", "公司"])]
                for l in lines[:15]:
                    print("  ", l)
            
            tables = page.extract_tables() or []
            for t_idx, table in enumerate(tables, 1):
                for r_idx, row in enumerate(table):
                    row_cells = [str(c).strip() for c in row if c]
                    row_str = " ".join(row_cells)
                    if any(k in row_str for k in ["股票", "股", "公司", "所有人", "面額"]) and "本欄空白" not in row_str:
                        print(f"  Table P{page_num} T{t_idx} R{r_idx}:", row_cells)
