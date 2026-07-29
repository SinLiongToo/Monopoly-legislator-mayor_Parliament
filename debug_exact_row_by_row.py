import pdfplumber
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pdf_path = "./downloads_priso/上官秋燕_財產申報_7.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[2] # Page 3
    tables = page.extract_tables() or []
    for t_idx, table in enumerate(tables, 1):
        print(f"\n--- Table {t_idx} ---")
        for r_idx, row in enumerate(table):
            print(f"  Row {r_idx}: {row}")
