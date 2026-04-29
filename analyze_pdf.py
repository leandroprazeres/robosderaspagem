import pdfplumber
import pandas as pd
import os

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"

def analyze_pdf(path):
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"--- Page {i+1} ---")
            tables = page.extract_tables()
            if tables:
                for table_idx, table in enumerate(tables):
                    print(f"Table {table_idx + 1}:")
                    # Print first 2 rows for inspection
                    for row in table[:2]:
                        print(row)
            else:
                # If no table, print snippet of text
                text = page.extract_text()
                if text:
                    print(text[:500])
            print("\n")

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        analyze_pdf(pdf_path)
    else:
        print(f"File not found: {pdf_path}")
