import pdfplumber

prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"

with pdfplumber.open(prova_pdf) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"--- Page {i+1} ---")
            print(text[:2000])
            print("\n" + "="*50 + "\n")
        if i > 5: # Just first 6 pages
            break
