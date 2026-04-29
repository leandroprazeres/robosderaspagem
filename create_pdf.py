import os
from fpdf import FPDF

txt_dir = "/Users/prazel01/.gemini/antigravity/scratch/extracted_emails"
output_pdf = "/Users/prazel01/.gemini/antigravity/scratch/Relatorio_Emails_Consolidado.pdf"

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Relatório de Emails Extraídos', border=True, align='C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("helvetica", size=10)

txt_files = [f for f in os.listdir(txt_dir) if f.endswith(".txt")]
txt_files.sort()

for i, txt_file in enumerate(txt_files):
    file_path = os.path.join(txt_dir, txt_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(0, 10, f"Arquivo {i+1}: {txt_file}", ln=True)
    pdf.set_font("helvetica", size=10)
    
    # Clean non-latin-1 characters for basic FPDF
    clean_content = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_content)
    pdf.ln(10)
    pdf.cell(0, 0, "", "T", ln=True) # Divider
    pdf.ln(5)

pdf.output(output_pdf)
print(f"PDF created at: {output_pdf}")
