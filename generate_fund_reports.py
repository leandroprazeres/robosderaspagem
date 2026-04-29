import pdfplumber
import pandas as pd
import re
import os
from fpdf import FPDF

pdf_path = "/Users/prazel01/Downloads/Decisão Carbono Oculto.pdf"
xlsx_output = "/Users/prazel01/.gemini/antigravity/scratch/Fundos_e_CNPJs.xlsx"
pdf_output = "/Users/prazel01/.gemini/antigravity/scratch/Tabela_Fundos_CNPJs.pdf"

def extract_data(path):
    data = []
    # Identified pages 17-20 as the range
    pages_to_extract = range(16, 20) # 0-indexed
    
    cnpj_pattern = re.compile(r"CNPJ:\s*([\d\./-]+)")
    
    with pdfplumber.open(path) as pdf:
        ordinal = 1
        for p_idx in pages_to_extract:
            page = pdf.pages[p_idx]
            text = page.extract_text()
            if not text:
                continue
            
            # Split text by lines and look for Fund names followed by CNPJs
            lines = text.split('\n')
            current_fundo = None
            
            for line in lines:
                # Basic check for Fund names (usually uppercase)
                # This logic might need refinement based on exact text layout
                if "FUNDO DE" in line.upper() or "FII" in line.upper():
                    # Check if line contains CNPJ too
                    cnpj_match = cnpj_pattern.search(line)
                    if cnpj_match:
                        fundo_name = line[:cnpj_match.start()].strip().strip(",").strip(":")
                        cnpj = cnpj_match.group(1)
                        data.append({"n. ordinal": ordinal, "nome de fundo": fundo_name, "n. CNPJ": cnpj})
                        ordinal += 1
                        current_fundo = None
                    else:
                        current_fundo = line.strip()
                elif current_fundo and "CNPJ:" in line:
                    cnpj_match = cnpj_pattern.search(line)
                    if cnpj_match:
                        cnpj = cnpj_match.group(1)
                        data.append({"n. ordinal": ordinal, "nome de fundo": current_fundo, "n. CNPJ": cnpj})
                        ordinal += 1
                        current_fundo = None
    return data

def generate_reports(data):
    df = pd.DataFrame(data)
    
    # Generate XLSX
    df.to_excel(xlsx_output, index=False)
    print(f"XLSX created at: {xlsx_output}")
    
    # Generate PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Tabela de Fundos e CNPJs", ln=True, align="C")
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(20, 10, "n. ord.", border=1)
    pdf.cell(120, 10, "Nome do Fundo", border=1)
    pdf.cell(50, 10, "CNPJ", border=1, ln=True)
    
    # Table Rows
    pdf.set_font("helvetica", size=9)
    for _, row in df.iterrows():
        # Handle wrap for long fund names
        start_y = pdf.get_y()
        pdf.multi_cell(120, 10, str(row["nome de fundo"]), border=1)
        end_y = pdf.get_y()
        height = end_y - start_y
        
        pdf.set_y(start_y)
        pdf.cell(20, height, str(row["n. ordinal"]), border=1)
        pdf.set_x(150) # Move to CNPJ column
        pdf.cell(50, height, str(row["n. CNPJ"]), border=1, ln=True)
    
    pdf.output(pdf_output)
    print(f"PDF created at: {pdf_output}")

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        extracted_data = extract_data(pdf_path)
        if extracted_data:
            generate_reports(extracted_data)
        else:
            print("No data extracted.")
    else:
        print(f"File not found: {pdf_path}")
