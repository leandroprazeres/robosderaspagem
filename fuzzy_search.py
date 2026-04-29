import pdfplumber
import re

prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"

def fuzzy_find(path, keywords):
    print(f"Searching for keywords: {keywords}")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = (page.extract_text() or "").lower()
            found = True
            for k in keywords:
                if k.lower() not in text:
                    found = False
                    break
            if found:
                print(f"FOUND ON PAGE {i+1}:")
                # Find the sentence
                idx = text.find(keywords[0].lower())
                print(text[max(0, idx-100):idx+300])
                print("-" * 50)

if __name__ == "__main__":
    # Trying the specific phrase parts
    fuzzy_find(prova_pdf, ["primeiro", "período", "segundo", "parágrafo"])
    fuzzy_find(prova_pdf, ["Linguagem", "Simples", "apesar"])
