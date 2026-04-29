import pdfplumber
import re
import pandas as pd
import os
from fpdf import FPDF

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"
xlsx_output = "/Users/prazel01/.gemini/antigravity/scratch/Entidades_CNPJs_Owners.xlsx"
pdf_output = "/Users/prazel01/.gemini/antigravity/scratch/Relatorio_Entidades_Completo.pdf"

# Regex for CNPJ
cnpj_regex = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"

def extract_entities_and_owners(path):
    all_data = []
    seen_cnpjs = {} # To avoid basic duplicates but keep context if different
    
    with pdfplumber.open(path) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Find all CNPJs on the page
            matches = list(re.finditer(cnpj_regex, text))
            
            for match in matches:
                cnpj = match.group(0)
                start, end = match.span()
                
                # Context window: 200 chars before and after
                before = text[max(0, start-250):start]
                after = text[end:min(len(text), end+250)]
                
                # Heuristic for Entity Name: Usually before the CNPJ, often in UPPERCASE or starting nearby
                # Many entries look like "COMPANY NAME (CNPJ ...)"
                entity_name = "Não identificado"
                owner_info = "Não identificado"
                
                # Try to find name in parentheses or right before
                # Look for uppercase blocks or specific words before match
                lines_before = before.split('\n')
                if lines_before:
                    target_line = lines_before[-1].strip()
                    # If line ends with opening bracket or parenthesis
                    if target_line.endswith("(") or target_line.endswith("["):
                         target_line = target_line[:-1].strip()
                    
                    # If very short, maybe it's on the line above
                    if len(target_line) < 5 and len(lines_before) > 1:
                        target_line = lines_before[-2].strip() + " " + target_line
                    
                    entity_name = target_line.strip(", ").strip(":")
                
                # Heuristic for Owners/Partners: Look for "titularidade de", "sócio", "proprietário", "administrado por"
                combined_context = (before + " " + cnpj + " " + after).lower()
                # Search for specific terms in the vicinity
                owner_keywords = ["titularidade de", "sócio", "proprietário", "administrado por", "gestora:", "administradora:", "sob o comando de"]
                
                for kw in owner_keywords:
                    if kw in combined_context:
                        # Extract 100 chars after the keyword
                        kw_pos = combined_context.find(kw)
                        extracted = combined_context[kw_pos:kw_pos+150].split('\n')[0].strip()
                        owner_info = extracted
                        break
                
                # Clean up entity name if it picked up headers or generic text
                if "TRIBUNAL DE JUSTIÇA" in entity_name or "CEP" in entity_name:
                    entity_name = "Verificar contexto"

                all_data.append({
                    "Entidade": entity_name,
                    "CNPJ": cnpj,
                    "Proprietários/Relacionados": owner_info,
                    "Página": p_idx + 1
                })
                
    return all_data

def generate_reports(data):
    df = pd.DataFrame(data)
    # Deduplicate based on CNPJ and Entity (to keep different contexts if relevant)
    df = df.drop_duplicates(subset=["CNPJ", "Entidade"])
    df.insert(0, "n. ordinal", range(1, len(df) + 1))
    
    # Save XLSX
    df.to_excel(xlsx_output, index=False)
    print(f"XLSX created at: {xlsx_output}")
    
    # Save PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Use a font that might better handle Unicode if needed, or keep simple
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Relatório Geral de Entidades e CNPJs", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 8)
    # Headers
    col_widths = [10, 50, 40, 70, 15]
    headers = ["Ord.", "Entidade", "CNPJ", "Relacionados", "Pág."]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, border=1)
    pdf.ln()
    
    pdf.set_font("helvetica", size=7)
    for _, row in df.iterrows():
        # Get max height for row
        # Multi-cell for Entidade and Relacionados
        entidade = str(row["Entidade"])[:100].encode('latin-1', 'replace').decode('latin-1')
        relacionados = str(row["Proprietários/Relacionados"])[:150].encode('latin-1', 'replace').decode('latin-1')
        
        # We'll use a simple multi-cell height calculation or just fixed height with truncation for PDF
        # To avoid complex table logic in fpdf, let's keep it readable
        pdf.cell(col_widths[0], 8, str(row["n. ordinal"]), border=1)
        pdf.cell(col_widths[1], 8, entidade[:40], border=1)
        pdf.cell(col_widths[2], 8, str(row["CNPJ"]), border=1)
        pdf.cell(col_widths[3], 8, relacionados[:60], border=1)
        pdf.cell(col_widths[4], 8, str(row["Página"]), border=1)
        pdf.ln()
    
    pdf.output(pdf_output)
    print(f"PDF created at: {pdf_output}")

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        data = extract_entities_and_owners(pdf_path)
        if data:
            generate_reports(data)
        else:
            print("No CNPJs found.")
    else:
        print(f"File not found: {pdf_path}")
