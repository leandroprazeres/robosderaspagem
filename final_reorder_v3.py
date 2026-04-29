import pdfplumber
import re
import pandas as pd
from fpdf import FPDF

# Paths
gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V3.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V3.pdf"

def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def extract_prova_correctly(path):
    full_text = ""
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extract words with their bounding boxes
            words = page.extract_words()
            # Sort by top first, then left. 
            # Note: For dual-column, we usually want to group by column first.
            # But let's try a simple sort and see.
            # actually better: sort by top (row), then left (position in row)
            words.sort(key=lambda x: (x['top'], x['x0']))
            
            page_text = ""
            current_top = -1
            for w in words:
                if abs(w['top'] - current_top) > 2: # New line
                    page_text += "\n"
                else:
                    page_text += " "
                page_text += w['text']
                current_top = w['top']
            
            full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
    return full_text

def extract_gabarito(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    
    # Pattern to catch: original_num [text] [certo/errado]
    pattern = re.compile(r"^(\d+)\s+(.*?)\s+(certo|errado)$", re.IGNORECASE | re.MULTILINE)
    items = []
    for match in pattern.finditer(text):
        original_text = match.group(2).strip()
        items.append({
            "orig_num": int(match.group(1)),
            "orig_prompt": original_text,
            "resp": match.group(3).strip(),
            "norm_prompt": normalize(original_text)
        })
    return items

def find_true_order(full_prova_text, items):
    norm_prova = normalize(full_prova_text)
    
    results = []
    for item in items:
        # We'll try to find the earliest occurrence of a significant part of the phrase
        prompt = item["norm_prompt"]
        snippets = [
            prompt[:min(30, len(prompt))], # Start
            prompt[len(prompt)//2 : len(prompt)//2 + 30], # Middle
            prompt[-30:] if len(prompt) > 30 else "" # End
        ]
        
        best_pos = -1
        for s in snippets:
            if not s: continue
            pos = norm_prova.find(s)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        results.append({
            **item,
            "found_pos": best_pos
        })
    
    # Sort by pos. 
    # If not found, put at the very end to be safe.
    results.sort(key=lambda x: x["found_pos"] if x["found_pos"] != -1 else 1e18)
    
    for i, res in enumerate(results):
        res["new_num"] = i + 1
        
    return results

if __name__ == "__main__":
    items = extract_gabarito(gabarito_pdf)
    prova_text = extract_prova_correctly(prova_pdf)
    
    # Debug: Save prova text to inspect
    with open("/tmp/prova_v3.txt", "w") as f:
        f.write(prova_text)
        
    ordered = find_true_order(prova_text, items)
    
    # Check if the user's specific first question is actually at position 1
    # User's #1: "No primeiro período do segundo parágrafo…"
    print("\n--- NEW ORDER VERIFICATION ---")
    for r in ordered[:15]:
        print(f"#{r['new_num']} (Orig #{r['orig_num']}): {r['orig_prompt'][:50]}... [Pos: {r['found_pos']}]")
        
    # Generate XLSX
    df = pd.DataFrame(ordered)
    df = df[['new_num', 'orig_num', 'orig_prompt', 'resp']]
    df.columns = ['Ordem_Prova', 'Num_Original', 'Questao', 'Gabarito']
    df.to_excel(output_xlsx, index=False)
    
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Gabarito Reordenado pela Prova (V3 - Final)", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(15, 8, "Prova", 1)
    pdf.cell(15, 8, "Orig.", 1)
    pdf.cell(130, 8, "Enunciado", 1)
    pdf.cell(25, 8, "Resp.", 1, ln=True)
    pdf.set_font("helvetica", size=7)
    for res in ordered:
        txt = res["orig_prompt"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 6, str(res["new_num"]), 1)
        pdf.cell(15, 6, str(res["orig_num"]), 1)
        pdf.cell(130, 6, txt[:85], 1)
        pdf.cell(25, 6, res["resp"], 1, ln=True)
    pdf.output(output_pdf)
    
    print("\nFiles saved to scratch.")
