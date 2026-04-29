import re
import difflib
import pandas as pd
from fpdf import FPDF
import os

# Paths
gabarito_txt = "/tmp/gabarito.txt"
prova_txt = "/tmp/prova.txt"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Reordenado.xlsx"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Gabarito_Reordenado.pdf"

def parse_gabarito(text):
    lines = text.split('\n')
    parsed = []
    # Simplified pattern to catch the columns
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
    ordered_results = []
    clean_prova = re.sub(r'\s+', ' ', prova_text)
    
    for item in gabarito_items:
        resumo = item["enunciado_resumo"]
        # Try direct find first
        search_snippet = resumo[:min(40, len(resumo))]
        pos = clean_prova.find(search_snippet)
        
        if pos == -1:
            # Try a slightly shorter snippet or look for key words
            words = resumo.split()
            if len(words) >= 3:
                short_search = " ".join(words[:4])
                pos = clean_prova.find(short_search)
        
        # If still not found, push to end to avoid blocking
        if pos == -1:
            pos = 999999 + item["original_num"]
            
        ordered_results.append({
            **item,
            "found_pos": pos
        })
    
    # Sort by the position found in the prova
    ordered_results.sort(key=lambda x: x["found_pos"])
    
    for i, item in enumerate(ordered_results):
        item["new_num"] = i + 1
        
    return ordered_results

def generate_pdf(data, path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Gabarito Reordenado conforme Prova_OCR.pdf", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9)
    # Headers
    pdf.cell(15, 8, "Novo #", 1)
    pdf.cell(15, 8, "Ant. #", 1)
    pdf.cell(130, 8, "Enunciado (Resumo)", 1)
    pdf.cell(25, 8, "Resposta", 1, ln=True)
    
    pdf.set_font("Arial", size=8)
    for item in data:
        enunc = item["enunciado_resumo"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(15, 7, str(item["new_num"]), 1)
        pdf.cell(15, 7, str(item["original_num"]), 1)
        pdf.cell(130, 7, enunc[:80], 1)
        pdf.cell(25, 7, item["resposta"], 1, ln=True)
        
    pdf.output(path)

if __name__ == "__main__":
    if not os.path.exists(gabarito_txt) or not os.path.exists(prova_txt):
        print("Missing required text files.")
    else:
        with open(gabarito_txt, "r", encoding="utf-8") as f:
            g_text = f.read()
        with open(prova_txt, "r", encoding="utf-8") as f:
            p_text = f.read()
            
        gabarito_items = parse_gabarito(g_text)
        print(f"Parsed {len(gabarito_items)} items.")
        
        ordered_data = find_question_order(p_text, gabarito_items)
        
        # Save XLSX
        df = pd.DataFrame(ordered_data)
        if not df.empty:
            df = df[['new_num', 'original_num', 'enunciado_resumo', 'resposta']]
            df.columns = ['Questão (Nova)', 'Questão (Original)', 'Enunciado Resumido', 'Resposta']
            df.to_excel(output_xlsx, index=False)
            print(f"Extracted {len(ordered_data)} questions.")
            
            generate_pdf(ordered_data, output_pdf)
            print("Successfully reordered and generated reports.")
        else:
            print("No items to save.")
