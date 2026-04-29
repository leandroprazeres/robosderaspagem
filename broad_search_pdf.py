import pdfplumber
import os

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"

def broad_search(path):
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Look for "fundo" and "CNPJ" on the same page
            if "fundo" in text.lower() and "cnpj" in text.lower():
                print(f"--- Fundo & CNPJ Page {i+1} ---")
                print(text[:2000]) # Print first 2000 chars
                print("-" * 30)

if __name__ == "__main__":
    broad_search(pdf_path)
