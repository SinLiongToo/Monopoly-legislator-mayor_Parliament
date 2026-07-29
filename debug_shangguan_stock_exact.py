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
        for page_num, page in enumerate(pdf.pages, 1):
            t = page.extract_text() or ""
            if "1.股票" in t or "110,900" in t or "中鋼" in t:
                print(f"--- Page {page_num} Stock Table ---")
                tables = page.extract_tables() or []
                for t_idx, table in enumerate(tables, 1):
                    for r_idx, row in enumerate(table):
                        row_cells = [str(c).strip().replace("\n", "") for c in row if c]
                        print(f"  P{page_num} T{t_idx} R{r_idx}: {row_cells}")
