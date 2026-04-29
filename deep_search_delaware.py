import pdfplumber
import os

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"

def deep_search_delaware(path):
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Case insensitive search for Delaware
            if "delaware" in text.lower():
                print(f"--- DELAWARE FOUND ON PAGE {i+1} ---")
                # Print 500 characters around the match
                idx = text.lower().find("delaware")
                print(text[max(0, idx-250):min(len(text), idx+250)])
                print("-" * 50)

if __name__ == "__main__":
    deep_search_delaware(pdf_path)
