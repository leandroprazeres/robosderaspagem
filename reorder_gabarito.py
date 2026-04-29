import re
import difflib
import pandas as pd
from fuzzywuzzy import fuzz
from fpdf import FPDF

# Paths
gabarito_txt = "/tmp/gabarito.txt"
prova_txt = "/tmp/prova.txt"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Reordenado.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Reordenado.pdf"

def parse_gabarito(text):
    # The gabarito looks like: "1 Seria mantida a correção... certo"
    # or "Questão Enunciado Resposta \n 1 ... certo"
    lines = text.split('\n')
    parsed = []
    # Pattern: ^(\d+) (.*) (certo|errado)$
    pattern = re.compile(r"^(\d+)\s+(.*?)\s+(certo|errado)$", re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            parsed.append({
                "original_num": int(match.group(1)),
                "enunciado_resumo": match.group(2).strip(),
                "resposta": match.group(3).strip()
            })
    return parsed

def find_question_order(prova_text, gabarito_items):
    # We need to find where each "enunciado_resumo" appears in the prova_text
    # and use its position to sort.
    ordered_results = []
    
    # Pre-process prova text to be more searchable
    # Remove excessive newlines but keep some structure
    clean_prova = re.sub(r'\s+', ' ', prova_text)
    
    for item in gabarito_items:
        resumo = item["enunciado_resumo"]
        # Use fuzzy search to find the index of the most similar snippet in the prova
        # This is tricky because the resumo is short. 
        # Better: Search for the literal string first, then fuzzy.
        
        # Searching for the first 30-50 chars of the resumo in the cleaned prova
        search_snippet = resumo[:50]
        pos = clean_prova.find(search_snippet)
        
        if pos == -1:
            # Try fuzzy if not found
            # (In a real scenario we'd chunk the prova and find best match)
            # For now, let's assume direct or partial match works
            pos = 999999 # Placeholder for not found
            
        ordered_results.append({
            **item,
            "found_pos": pos
        })
    
    # Sort by the position found in the prova
    ordered_results.sort(key=lambda x: x["found_pos"])
    
    # Assign new numbers based on the found order
    for i, item in enumerate(ordered_results):
        item["new_num"] = i + 1
        
    return ordered_results

def generate_pdf(data, path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Gabarito Reordenado conforme Prova_OCR.pdf", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 10, "Novo #", 1)
    pdf.cell(15, 10, "Ant. #", 1)
    pdf.cell(120, 10, "Enunciado (Resumo)", 1)
    pdf.cell(30, 10, "Resposta", 1, ln=True)
    
    pdf.set_font("Arial", size=9)
    for item in data:
        # Avoid latin-1 encoding errors
        enunciado = item["enunciado_resumo"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 8, str(item["new_num"]), 1)
        pdf.cell(15, 8, str(item["original_num"]), 1)
        pdf.cell(120, 8, enunciado[:70], 1)
        pdf.cell(30, 8, item["resposta"], 1, ln=True)
        
    pdf.output(path)

if __name__ == "__main__":
    with open(gabarito_txt, "r", encoding="utf-8") as f:
        g_text = f.read()
    with open(prova_txt, "r", encoding="utf-8") as f:
        p_text = f.read()
        
    gabarito_items = parse_gabarito(g_text)
    print(f"Parsed {len(gabarito_items)} items from gabarito.")
    
    if not gabarito_items:
        # Try a more relaxed parse if literal matching fails
        print("Detailed parsing failed, check regex.")
    
    ordered_data = find_question_order(p_text, gabarito_items)
    
    # Save results
    df = pd.DataFrame(ordered_data)
    df = df[['new_num', 'original_num', 'enunciado_resumo', 'resposta']]
    df.columns = ['Questão (Nova)', 'Questão (Original)', 'Enunciado Resumido', 'Resposta']
    df.to_excel(output_xlsx, index=False)
    print(f"Excel saved to {output_xlsx}")
    
    generate_pdf(ordered_data, output_pdf)
    print(f"PDF saved to {output_pdf}")
