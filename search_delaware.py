import pandas as pd
import os

assets_path = "/Users/prazel01/.gemini/antigravity/scratch/Ativos_Dos_Fundos.xlsx"
entities_path = "/Users/prazel01/Downloads/Entidades_CNPJs_Owners.xlsx"

def find_delaware_links():
    # Terms to search for
    search_terms = ["delaware", "de", "usa", "unidos", "states"]
    # specifically delaware but broad enough to find mentions
    
    print("--- Searching in Ativos_Dos_Fundos.xlsx ---")
    if os.path.exists(assets_path):
        df_assets = pd.read_excel(assets_path)
        # Convert all to string and lowercase for search
        mask = df_assets.apply(lambda x: x.astype(str).str.contains('delaware', case=False, na=False)).any(axis=1)
        matches_assets = df_assets[mask]
        if not matches_assets.empty:
            print(f"Found {len(matches_assets)} matches in assets.")
            print(matches_assets[['CNPJ_FUNDO_CLASSE', 'DENOM_SOCIAL', 'EMISSOR', 'DS_ATIVO']])
        else:
            print("No matches found in assets.")
    
    print("\n--- Searching in Entidades_CNPJs_Owners.xlsx ---")
    if os.path.exists(entities_path):
        df_entities = pd.read_excel(entities_path)
        mask_ent = df_entities.apply(lambda x: x.astype(str).str.contains('delaware', case=False, na=False)).any(axis=1)
        matches_ent = df_entities[mask_ent]
        if not matches_ent.empty:
            print(f"Found {len(matches_ent)} matches in entities/owners.")
            print(matches_ent[['Entidade', 'CNPJ', 'Proprietários/Relacionados']])
        else:
            print("No matches found in entities.")

if __name__ == "__main__":
    find_delaware_links()
