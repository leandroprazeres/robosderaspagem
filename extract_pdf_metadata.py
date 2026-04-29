import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    import sys
    print("pypdf not installed.")
    sys.exit(1)

def extract_pdf_metadata(pdf_url):
    if not pdf_url:
        return {"PDF_URL": "", "PDF_Author": "", "PDF_Creator": "", "PDF_Producer": "", "Meta_Status": "Sem URL"}
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(pdf_url, headers=headers, timeout=15)
        r.raise_for_status()
        
        # Read PDF from bytes
        pdf_file = io.BytesIO(r.content)
        reader = PdfReader(pdf_file)
        meta = reader.metadata
        if not meta:
            return {"PDF_URL": pdf_url, "PDF_Author": "N/A", "PDF_Creator": "N/A", "PDF_Producer": "N/A", "Meta_Status": "Sem metadados no arquivo"}
            
        return {
            "PDF_URL": pdf_url,
            "PDF_Author": str(meta.author or ""),
            "PDF_Creator": str(meta.creator or ""),
            "PDF_Producer": str(meta.producer or ""),
            "Meta_Status": "OK"
        }
    except Exception as e:
        return {"PDF_URL": pdf_url, "PDF_Author": "", "PDF_Creator": "", "PDF_Producer": "", "Meta_Status": f"Erro: {str(e)[:40]}"}

def get_texto_inicial_url(codigo_materia):
    url = f"https://legis.senado.gov.br/dadosabertos/materia/textos/{codigo_materia}"
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # If "TextoMateria" is returned
            textos = data.get("TextoMateria", {}).get("Materia", {}).get("Textos", {}).get("Texto", [])
            if isinstance(textos, dict):
                textos = [textos]
                
            # Prefer text containing 'inicial', 'original', 'apresenta'
            for t in textos:
                desc = t.get("DescricaoTexto", "").lower()
                url_doc = t.get("UrlTexto", "")
                if "inicial" in desc or "original" in desc or "apresenta" in desc:
                    return url_doc
            # Otherwise return the first available
            if textos:
                return textos[0].get("UrlTexto", "")
    except Exception as e:
        pass
    return ""

def process_item(item):
    if item["Categoria"] == "Proposição":
        codigo = item.get("CodigoMateria")
        if codigo:
            pdf_url = get_texto_inicial_url(codigo)
            item["Link Documento Final"] = pdf_url
        else:
            item["Link Documento Final"] = item.get("Link Documento")
    else:
        # Emenda already has direct link in most cases
        item["Link Documento Final"] = item.get("Link Documento")
        
    meta = extract_pdf_metadata(item["Link Documento Final"])
    item.update(meta)
    return item

print("Fetching refined list of documents for Senator Flávio Bolsonaro (ID 5894)...")

# --- Fetch Autorias ---
headers = {"Accept": "application/json"}
r_autoria = requests.get("https://legis.senado.gov.br/dadosabertos/senador/5894/autorias", headers=headers)
data_autoria = r_autoria.json()
autorias_raw = data_autoria.get("MateriasAutoriaParlamentar", {}).get("Parlamentar", {}).get("Autorias", {}).get("Autoria", [])
if isinstance(autorias_raw, dict): autorias_raw = [autorias_raw]

parsed_items = []
for item in autorias_raw:
    if item.get("IndicadorAutorPrincipal") != "Sim": continue
    materia = item.get("Materia", {})
    parsed_items.append({
        "Categoria": "Proposição",
        "Numero do Projeto": f"{materia.get('Sigla', '')} {materia.get('Numero', '')}/{materia.get('Ano', '')}",
        "Ementa / Resumo": materia.get("Ementa", ""),
        "CodigoMateria": materia.get("Codigo", ""),
        "Link Documento": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{materia.get('Codigo', '')}"
    })

# --- Fetch Emendas ---
r_emendas = requests.get("https://legis.senado.gov.br/dadosabertos/processo/emenda", params={"codigoParlamentarAutor": "5894"}, headers=headers)
data_emendas = r_emendas.json()
if isinstance(data_emendas, list):
    emendas_raw = data_emendas
else:
    emendas_raw = data_emendas.get("EmendaList", {}).get("Emendas", {}).get("Emenda", [])
if isinstance(emendas_raw, dict): emendas_raw = [emendas_raw]

for em in emendas_raw:
    autoria = em.get("autoria", "")
    if "," in autoria: continue
    parsed_items.append({
        "Categoria": "Emenda",
        "Numero do Projeto": em.get("identificacao", f"Emenda {em.get('numero')}"),
        "Ementa / Resumo": em.get("tipo", "Emenda"),
        "CodigoMateria": "",
        "Link Documento": em.get("urlDocumentoEmenda", "")
    })

print(f"Total documents to process: {len(parsed_items)}")
print("Downloading PDFs and extracting metadata in parallel (this may take a few minutes)...")

processed_results = []
threads_count = 10 # 10 parallel downloads
completed = 0

with ThreadPoolExecutor(max_workers=threads_count) as executor:
    futures = {executor.submit(process_item, item): item for item in parsed_items}
    for future in as_completed(futures):
        completed += 1
        try:
            res = future.result()
            processed_results.append(res)
            if completed % 20 == 0:
                print(f"Processed {completed} / {len(parsed_items)}...")
        except Exception as e:
            print(f"Error processing item: {e}")

print("Extraction completed. Building DataFrame...")

df = pd.DataFrame(processed_results)
df = df.drop(columns=["CodigoMateria", "Link Documento Final"])
# Reorder columns to a clean format
cols = ["Categoria", "Numero do Projeto", "Ementa / Resumo", "PDF_Author", "PDF_Creator", "PDF_Producer", "Meta_Status", "PDF_URL", "Link Documento"]
df = df[[c for c in cols if c in df.columns]]

output_file = "/Users/prazel01/.gemini/antigravity/scratch/Projetos_Metadados_Flavio_Bolsonaro.xlsx"
df.to_excel(output_file, index=False)
print(f"Saved successfully to: {output_file}")
