import requests
import json
import pandas as pd

print("Starting extraction for Senator Flávio Bolsonaro (ID 5894) - REFINED...")

# --- 1. Fetching Autoria ---
url_autorias = "https://legis.senado.gov.br/dadosabertos/senador/5894/autorias"
headers = {"Accept": "application/json"}
print("Fetching Autorias...")
r_autoria = requests.get(url_autorias, headers=headers)
r_autoria.raise_for_status()
data_autoria = r_autoria.json()

autorias_raw = data_autoria.get("MateriasAutoriaParlamentar", {}).get("Parlamentar", {}).get("Autorias", {}).get("Autoria", [])
if isinstance(autorias_raw, dict):
    autorias_raw = [autorias_raw]

parsed_autorias = []
for item in autorias_raw:
    # FILTRO: Apenas autor principal
    if item.get("IndicadorAutorPrincipal") != "Sim":
        continue
        
    materia = item.get("Materia", {})
    tipo = "Proposição"
    sigla = materia.get("Sigla", "")
    numero = materia.get("Numero", "")
    ano = materia.get("Ano", "")
    data = materia.get("Data", "")
    ementa = materia.get("Ementa", "")
    codigo = materia.get("Codigo", "")
    link = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo}" if codigo else ""
    
    parsed_autorias.append({
        "Categoria": tipo,
        "Identificacao": f"{sigla} {numero}/{ano}" if ano else f"{sigla} {numero}",
        "Data Apresentacao": data,
        "Ementa / Descricao": ementa,
        "Link Documento": link,
        "Autoria Restrita": "Sim (Autor Principal)"
    })

print(f"  -> Found {len(parsed_autorias)} autorias principais.")

# --- 2. Fetching Emendas ---
url_emendas = "https://legis.senado.gov.br/dadosabertos/processo/emenda"
params = {"codigoParlamentarAutor": "5894"}
print("Fetching Emendas...")
r_emendas = requests.get(url_emendas, params=params, headers=headers)
r_emendas.raise_for_status()
data_emendas = r_emendas.json()

if isinstance(data_emendas, list):
    emendas_raw = data_emendas
else:
    emendas_raw = data_emendas.get("EmendaList", {}).get("Emendas", {}).get("Emenda", [])
    
if isinstance(emendas_raw, dict):
    emendas_raw = [emendas_raw]
    
parsed_emendas = []
for em in emendas_raw:
    autoria = em.get("autoria", "")
    # FILTRO: Apenas emendas onde ele é o único autor ou o primeiro nome que aparece sozinho (evitando listas de dezenas de senadores)
    # A string usual para ele sozinho é algo como "Senador Flávio Bolsonaro (PSL/RJ)" ou "(PL/RJ)"
    # Se houver vírgula na autoria, geralmente significa múltiplos autores.
    if "," in autoria and not autoria.startswith("Senador Flávio Bolsonaro"):
        continue
    # Para ser mais rigoroso, vamos garantir que ele seja o único autor (sem vírgulas)
    if "," in autoria:
        continue
        
    tipo = "Emenda"
    ident = em.get("identificacao", f"Emenda {em.get('numero')}")
    data = em.get("dataApresentacao", "")
    ementa = em.get("tipo", "Emenda")
    link = em.get("urlDocumentoEmenda", "")
    
    parsed_emendas.append({
        "Categoria": tipo,
        "Identificacao": ident,
        "Data Apresentacao": data,
        "Ementa / Descricao": ementa,
        "Link Documento": link,
        "Autoria Restrita": "Sim (Autor Único)"
    })

print(f"  -> Found {len(parsed_emendas)} emendas exclusivas.")

# --- 3. Compile and Export ---
df = pd.DataFrame(parsed_autorias + parsed_emendas)
df["Data Temporaria"] = pd.to_datetime(df["Data Apresentacao"], errors="coerce")
df = df.sort_values(by="Data Temporaria", ascending=False).drop(columns=["Data Temporaria"])

output_file = "/Users/prazel01/.gemini/antigravity/scratch/Proposicoes_Flavio_Bolsonaro_Refinado.xlsx"
print(f"Exporting to {output_file}...")
df.to_excel(output_file, index=False)
print("Done!")
