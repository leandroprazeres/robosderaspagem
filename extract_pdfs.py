import pdfplumber
import os

pdf1_path = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
pdf2_path = "/Users/prazel01/Downloads/Prova_OCR.pdf"

def extract_and_preview(path, name):
    print(f"--- Extracting {name} ({path}) ---")
    with pdfplumber.open(path) as pdf:
        full_text = ""
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
                if i < 2: # Preview first 2 pages
                    print(f"Page {i+1} Preview:")
                    print(text[:1000])
                    print("-" * 30)
        
        # Save to tmp for inspection if needed
        output_txt = f"/tmp/{name}.txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Full text saved to {output_txt}")

if __name__ == "__main__":
    extract_and_preview(pdf1_path, "gabarito")
    print("\n" + "="*50 + "\n")
    extract_and_preview(pdf2_path, "prova")
