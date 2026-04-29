import pandas as pd
import os

xlsx_path = "/Users/prazel01/Downloads/Entidades_CNPJs_Owners.xlsx"
cda_dir = "/Users/prazel01/Downloads/cda_fi_202601"
output_xlsx = "/Users/prazel01/.gemini/antigravity/scratch/Ativos_Dos_Fundos.xlsx"

def extract_assets():
    # 1. Load target CNPJs
    df_funds = pd.read_excel(xlsx_path)
    target_cnpjs = df_funds['CNPJ'].unique().tolist()
    print(f"Targeting {len(target_cnpjs)} funds.")
    
    all_assets = []
    
    files = [f for f in os.listdir(cda_dir) if f.endswith(".csv")]
    
    for f in files:
        if "CONFID" in f or "PL" in f: # Skip confidentiality and PL-only files for now
            continue
            
        print(f"Processing {f}...")
        file_path = os.path.join(cda_dir, f)
        
        try:
            # Chunk processing to handle large files
            chunk_iter = pd.read_csv(file_path, sep=';', encoding='iso-8859-1', chunksize=50000)
            for chunk in chunk_iter:
                # Filter by CNPJ
                matched = chunk[chunk['CNPJ_FUNDO_CLASSE'].isin(target_cnpjs)]
                if not matched.empty:
                    # Generic asset identification
                    # Most blocks have common columns, but we'll adapt
                    subset = matched.copy()
                    subset['Origem_Arquivo'] = f
                    all_assets.append(subset)
                    
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    if all_assets:
        df_final = pd.concat(all_assets, ignore_index=True)
        # Select and reorder columns for clarity
        cols_to_keep = [
            'CNPJ_FUNDO_CLASSE', 'DENOM_SOCIAL', 'TP_APLIC', 'TP_ATIVO', 
            'EMISSOR', 'CPF_CNPJ_EMISSOR', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA', 
            'DS_ATIVO', 'QT_POS_FINAL', 'VL_MERC_POS_FINAL', 'Origem_Arquivo'
        ]
        # Keep only existing columns
        existing_cols = [c for c in cols_to_keep if c in df_final.columns]
        df_final = df_final[existing_cols]
        
        df_final.to_excel(output_xlsx, index=False)
        print(f"Extracted {len(df_final)} asset rows to {output_xlsx}")
    else:
        print("No matching assets found.")

if __name__ == "__main__":
    extract_assets()
