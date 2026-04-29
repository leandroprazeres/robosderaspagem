import pdfplumber
import re

prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"
gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"

def analyze_layout(path):
    print(f"--- Analyzing Layout of {path} ---")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n[Page {i+1}]")
            # Sort words by top then left to handle columns better
            words = page.extract_words(sort=True)
            # Reconstruct text from words
            lines = {}
            for w in words:
                y = round(w['top'], 1)
                lines.setdefault(y, []).append(w['text'])
            
            for y in sorted(lines.keys()):
                print(" ".join(lines[y]))
                
            if i >= 3: # Check first 4 pages
                break

def inspect_gabarito(path):
    print(f"\n--- Gabarito Contents ---")
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            print(page.extract_text())

if __name__ == "__main__":
    analyze_layout(prova_pdf)
    inspect_gabarito(gabarito_pdf)
