import pdfplumber
import re
import pandas as pd
from fpdf import FPDF

# Paths
gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
prova_pdf = "/Users/prazel01/Downloads/Prova_OCR.pdf"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V4.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V4.pdf"

def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def extract_columnar_text(path):
    full_text = ""
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Split page in two columns
            width = page.width
            height = page.height
            
            # Left Column
            left = page.crop((0, 0, width/2, height))
            left_text = left.extract_text() or ""
            
            # Right Column
            right = page.crop((width/2, 0, width, height))
            right_text = right.extract_text() or ""
            
            full_text += f"\n--- Page {i+1} LEFT ---\n{left_text}\n"
            full_text += f"\n--- Page {i+1} RIGHT ---\n{right_text}\n"
    return full_text

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
            "norm_prompt": normalize(match.group(2).strip())
        })
    return items

def find_true_order(full_text, items):
    norm_full = normalize(full_text)
    
    results = []
    for item in items:
        # Use a more robust search
        prompt = item["norm_prompt"]
        snippets = [prompt[:40], prompt[10:50] if len(prompt)>50 else prompt]
        
        pos = -1
        for s in snippets:
            if not s: continue
            pos = norm_full.find(s)
            if pos != -1:
                break
        
        results.append({
            **item,
            "found_pos": pos
        })
    
    # Sort
    results.sort(key=lambda x: x["found_pos"] if x["found_pos"] != -1 else 1e20)
    
    for idx, r in enumerate(results):
        r["new_num"] = idx + 1
    return results

if __name__ == "__main__":
    items = extract_gabarito(gabarito_pdf)
    text_v4 = extract_columnar_text(prova_pdf)
    
    with open("/tmp/prova_v4.txt", "w") as f:
        f.write(text_v4)
        
    ordered = find_true_order(text_v4, items)
    
    print("\n--- VERSION 4 ORDER ---")
    for r in ordered[:15]:
        print(f"#{r['new_num']} (Orig #{r['orig_num']}): {r['orig_prompt'][:60]}... [Pos: {r['found_pos']}]")
        
    # Save files
    df = pd.DataFrame(ordered)
    df = df[['new_num', 'orig_num', 'orig_prompt', 'resp']]
    df.columns = ['Questão Prova', 'N. Gabarito Original', 'Enunciado', 'Gabarito']
    df.to_excel(output_xlsx, index=False)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Gabarito Reordenado (V4 - Column Aware)", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(15, 8, "Prova", 1)
    pdf.cell(15, 8, "Orig.", 1)
    pdf.cell(130, 8, "Enunciado", 1)
    pdf.cell(25, 8, "Resp.", 1, ln=True)
    pdf.set_font("helvetica", size=7)
    for res in ordered:
        t = res["orig_prompt"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 6, str(res["new_num"]), 1)
        pdf.cell(15, 6, str(res["orig_num"]), 1)
        pdf.cell(130, 6, t[:85], 1)
        pdf.cell(25, 6, res["resp"], 1, ln=True)
    pdf.output(output_pdf)
    print("\nFiles saved to scratch.")
