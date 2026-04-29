import pdfplumber
import os
import re

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"

def broad_jurisdiction_search(path):
    # Common offshore/international jurisdictions or related terms
    terms = ["delaware", "cayman", "bvi", "virgin", "islands", "bahamas", "luxembourg", "luxemburgo", "offshore", "exterior", "estrangeiro"]
    
    matches = []
    
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            for term in terms:
                if term in text.lower():
                    # Extract context
                    matches.append({
                        "Page": i + 1,
                        "Term": term,
                        "Context": text[max(0, text.lower().find(term)-200):text.lower().find(term)+200]
                    })
    return matches

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        results = broad_jurisdiction_search(pdf_path)
        if results:
            print(f"Found {len(results)} potential jurisdiction-related mentions.")
            for r in results[:10]: # Print first 10
                print(f"--- Page {r['Page']} (Term: {r['Term']}) ---")
                print(r['Context'])
                print("-" * 30)
        else:
            print("No jurisdiction-related terms found.")
    else:
        print(f"File not found: {pdf_path}")
