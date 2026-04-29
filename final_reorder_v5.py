import re
import pandas as pd
from fpdf import FPDF
import pdfplumber
import difflib

gabarito_pdf = "/Users/prazel01/Downloads/gabarito_questoes.pdf"
prova_txt_path = "/tmp/prova_v4.txt"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V5.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Final_V5.pdf"

def extract_gabarito(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    pattern = re.compile(r"^(\d+)\s+(.*?)\s+(certo|errado)$", re.IGNORECASE | re.MULTILINE)
    items = []
    for match in pattern.finditer(text):
        items.append({
            "orig_num": int(match.group(1)),
            "prompt": match.group(2).strip(),
            "resp": match.group(3).strip()
        })
    return items

def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def solve_mapping():
    g_items = extract_gabarito(gabarito_pdf)
    with open(prova_txt_path, "r") as f:
        prova_text = f.read()
    
    # 1. Find all numbers followed by some text in the proof
    # Most Cebraspe questions are numbered like "1", "2", "3" at the start of a block
    # Or "| 1 ", "| 2 "
    q_matches = re.finditer(r"(?:^|[ \n|])(\d+)\s+([A-Z].*?)(?=\n\s*\d+\s+|---|Page|$)", prova_text, re.MULTILINE | re.DOTALL)
    
    proof_questions = []
    for m in q_matches:
        q_num = int(m.group(1))
        q_text = m.group(2).replace('\n', ' ').strip()
        if len(q_text) < 10: continue # Skip page numbers etc
        proof_questions.append({
            "proof_num": q_num,
            "text": q_text,
            "norm": normalize(q_text)
        })
    
    print(f"Detected {len(proof_questions)} questions in proof sequence.")
    
    final_mapping = []
    used_orig = set()
    
    # For each question in the proof sequence, find the best match in the gabarito
    for pq in proof_questions:
        best_match = None
        best_score = 0
        
        for gi in g_items:
            # Simple substring check first
            norm_gi = normalize(gi["prompt"])
            if norm_gi[:40] in pq["norm"] or pq["norm"][:40] in norm_gi:
                score = 1.0
            else:
                score = difflib.SequenceMatcher(None, pq["norm"][:100], norm_gi[:100]).ratio()
            
            if score > best_score:
                best_score = score
                best_match = gi
        
        if best_match and best_score > 0.4:
            # used_orig.add(best_match["orig_num"]) # In case of duplicates, keep going
            final_mapping.append({
                "ordem_prova": pq["proof_num"],
                "num_original": best_match["orig_num"],
                "enunciado": best_match["prompt"],
                "resp": best_match["resp"],
                "score": best_score
            })
            
    # Remove duplicates (keep first occurrence in proof)
    unique_mapping = []
    seen_ordem = set()
    for m in final_mapping:
        if m["ordem_prova"] not in seen_ordem:
            unique_mapping.append(m)
            seen_ordem.add(m["ordem_prova"])
            
    # Sort by proof number
    unique_mapping.sort(key=lambda x: x["ordem_prova"])
    
    return unique_mapping

if __name__ == "__main__":
    result = solve_mapping()
    print(f"Mapped {len(result)} questions successfully.")
    
    if result:
        print("\nTop 5 Final Mapping:")
        for r in result[:5]:
            print(f"Proof #{r['ordem_prova']} matched Orig #{r['num_original']}: {r['enunciado'][:60]}")

        # Save XLSX
        df = pd.DataFrame(result)
        df = df[['ordem_prova', 'num_original', 'enunciado', 'resp']]
        df.columns = ['Questão na Prova', 'N. Gabarito Original', 'Enunciado Resumido', 'Resposta']
        df.to_excel(output_xlsx, index=False)
        
        # Save PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Gabarito Reordenado (V5 - FINAL CORRETISSIMO)", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(15, 8, "Prova", 1)
        pdf.cell(15, 8, "Orig.", 1)
        pdf.cell(130, 8, "Enunciado", 1)
        pdf.cell(25, 8, "Resp.", 1, ln=True)
        pdf.set_font("helvetica", size=7)
        for r in result:
            txt = r["enunciado"].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(15, 6, str(r["ordem_prova"]), 1)
            pdf.cell(15, 6, str(r["num_original"]), 1)
            pdf.cell(130, 6, txt[:85], 1)
            pdf.cell(25, 6, r["resp"], 1, ln=True)
        pdf.output(output_pdf)
        print("\nSUCCESS: Files saved.")
    else:
        print("\nFAILURE: No mapping found.")
