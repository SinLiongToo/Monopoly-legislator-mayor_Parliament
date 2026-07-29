from parse_priso_individual_pdfs import consolidate_officer_parsed_data, parse_priso_pdf_full
import glob

pdf_files = sorted(glob.glob("./downloads_priso/*上官秋燕*.pdf"))

print("1. Parsing individual PDFs:")
for p in pdf_files:
    res = parse_priso_pdf_full(p)
    print(f"  {p}: stocksTotal={res['stocksTotal']}, stockList={res['stockList']}")

print("\n2. Consolidating data:")
data = consolidate_officer_parsed_data(pdf_files)
print("Consolidated stockList:", data["stockList"])
