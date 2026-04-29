import pdfplumber
import os
import re

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"

def find_table(path):
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Look for the header keywords
            if "ordinal" in text.lower() and "fundo" in text.lower() and "cnpj" in text.lower():
                print(f"--- Potential Header Found on Page {i+1} ---")
                print(text)
                print("-" * 30)
                
                # Check for tables on this page
                tables = page.extract_tables()
                if tables:
                    for t_idx, table in enumerate(tables):
                        print(f"Table {t_idx + 1} on Page {i+1}:")
                        for row in table:
                            print(row)
                print("\n")

if __name__ == "__main__":
    find_table(pdf_path)
