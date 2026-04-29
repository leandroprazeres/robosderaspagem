import pdfplumber
import re
import pandas as pd
from fpdf import FPDF

# Paths
gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Corrigido.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Corrigido.pdf"

def get_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def parse_gabarito(text):
    lines = text.split('\n')
    parsed = []
    # Pattern: ^(\d+) (.*) (certo|errado)$
    pattern = re.compile(r"^(\d+)\s+(.*?)\s+(certo|errado)$", re.IGNORECASE)
    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            parsed.append({
                "orig_num": int(match.group(1)),
                "prompt": match.group(2).strip(),
                "resp": match.group(3).strip()
            })
    return parsed

def find_true_order(prova_text, gabarito_items):
    # Standardize spaces for searching
    clean_prova = re.sub(r'\s+', ' ', prova_text)
    
    results = []
    for item in gabarito_items:
        prompt = item["prompt"]
        # Use first 60 chars for searching
        search_key = prompt[:60]
        pos = clean_prova.find(search_key)
        
        # If not found, try a middle snippet just in case of OCR noise at start
        if pos == -1 and len(prompt) > 80:
            search_key = prompt[20:80]
            pos = clean_prova.find(search_key)
            
        results.append({
            **item,
            "pos": pos
        })
    
    # Sort by pos. If pos is -1 (not found), put at the end
    results.sort(key=lambda x: x["pos"] if x["pos"] != -1 else 999999)
    
    for idx, item in enumerate(results):
        item["new_num"] = idx + 1
        
    return results

if __name__ == "__main__":
    g_text = get_text(gabarito_pdf)
    p_text = get_text(prova_pdf)
    
    items = parse_gabarito(g_text)
    print(f"Parsed {len(items)} items from gabarito.")
    
    ordered = find_true_order(p_text, items)
    
    # Print first few for verification against user example
    print("\nTop 5 ordered questions found:")
    for i in range(min(5, len(ordered))):
        print(f"New #{ordered[i]['new_num']} (Orig #{ordered[i]['orig_num']}): {ordered[i]['prompt'][:50]}... [{ordered[i]['pos']}]")
    
    # Save results
    df = pd.DataFrame(ordered)
    df = df[['new_num', 'orig_num', 'prompt', 'resp']]
    df.columns = ['Questão_Prova', 'Questão_Gabarito_Original', 'Enunciado_Resumido', 'Resposta']
    df.to_excel(output_xlsx, index=False)
    
    # PDF generation
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Gabarito Reordenado (CORRIGIDO)", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(15, 8, "Prova", 1)
    pdf.cell(15, 8, "Orig.", 1)
    pdf.cell(130, 8, "Enunciado", 1)
    pdf.cell(25, 8, "Resp.", 1, ln=True)
    pdf.set_font("helvetica", size=7)
    for item in ordered:
        e = item["prompt"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 6, str(item["new_num"]), 1)
        pdf.cell(15, 6, str(item["orig_num"]), 1)
        pdf.cell(130, 6, e[:85], 1)
        pdf.cell(25, 6, item["resp"], 1, ln=True)
    pdf.output(output_pdf)
    
    print(f"\nSaved to {output_xlsx} and {output_pdf}")
