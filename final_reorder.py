import re
import pandas as pd
from fpdf import FPDF
import pdfplumber

gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final.pdf"

def normalize(text):
    # Remove all non-alphanumeric and extra spaces
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def extract_gabarito(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    
    # Pattern to catch: original_num [text] [certo/errado]
    pattern = re.compile(r"^(\d+)\s+(.*?)\s+(certo|errado)$", re.IGNORECASE | re.MULTILINE)
    items = []
    for match in pattern.finditer(text):
        items.append({
            "orig_num": int(match.group(1)),
            "orig_prompt": match.group(2).strip(),
            "resp": match.group(3).strip(),
            "norm_prompt": normalize(match.group(2).strip())[:100] # Use first 100 normalized chars
        })
    return items

def find_order(prova_path, items):
    with pdfplumber.open(prova_path) as pdf:
        # Instead of full text, let's keep page info and position
        all_pages_text = []
        for i, page in enumerate(pdf.pages):
            all_pages_text.append(page.extract_text() or "")
            
    # Combine but keep track of indices
    full_prova_text = "\n".join(all_pages_text)
    norm_prova = normalize(full_prova_text)
    
    results = []
    for item in items:
        # Search for the normalized prompt in the normalized prova
        # Using a slightly shorter snippet for search
        search_key = item["norm_prompt"][:40] 
        pos = norm_prova.find(search_key)
        
        # If not found, try even shorter or middle
        if pos == -1 and len(item["norm_prompt"]) > 40:
             search_key = item["norm_prompt"][10:50]
             pos = norm_prova.find(search_key)

        results.append({
            **item,
            "found_pos": pos
        })
    
    # Sort by pos. Items not found go to the end.
    results.sort(key=lambda x: x["found_pos"] if x["found_pos"] != -1 else 1e12)
    
    for i, item in enumerate(results):
        item["new_pos"] = i + 1
        
    return results

if __name__ == "__main__":
    items = extract_gabarito(gabarito_pdf)
    print(f"Extracted {len(items)} items from gabarito.")
    
    ordered = find_order(prova_pdf, items)
    
    # Verification against user example:
    # "No primeiro período do segundo parágrafo" vs "Segundo o texto, apesar de a Linguagem Simples"
    print("\nOrder Verification:")
    for i in range(min(10, len(ordered))):
        print(f"#{ordered[i]['new_pos']} (Orig #{ordered[i]['orig_num']}): {ordered[i]['orig_prompt'][:50]}... [Pos: {ordered[i]['found_pos']}]")

    # Generate XLSX
    df = pd.DataFrame(ordered)
    df = df[['new_pos', 'orig_num', 'orig_prompt', 'resp']]
    df.columns = ['Ordem na Prova', 'N. Gabarito Original', 'Questão', 'Gabarito']
    df.to_excel(output_xlsx, index=False)
    
    # Generate PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Gabarito Reordenado pela Prova", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(15, 8, "Prova", 1)
    pdf.cell(15, 8, "Orig.", 1)
    pdf.cell(130, 8, "Enunciado", 1)
    pdf.cell(25, 8, "Resp.", 1, ln=True)
    
    pdf.set_font("helvetica", size=7)
    for item in ordered:
        txt = item["orig_prompt"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 6, str(item["new_pos"]), 1)
        pdf.cell(15, 6, str(item["orig_num"]), 1)
        pdf.cell(130, 6, txt[:80], 1)
        pdf.cell(25, 6, item["resp"], 1, ln=True)
        
    pdf.output(output_pdf)
    print(f"\nResults saved to scratch directory.")
