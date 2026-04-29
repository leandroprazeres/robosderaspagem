import pandas as pd
import os

xlsx_path = "/Users/prazel01/Downloads/Entidades_CNPJs_Owners.xlsx"
cda_dir = "/Users/prazel01/Downloads/cda_fi_202601"

def analyze_data():
    # 1. Read target CNPJs
    df_funds = pd.read_excel(xlsx_path)
    cnpjs = df_funds['CNPJ'].unique().tolist()
    print(f"Found {len(cnpjs)} unique CNPJs in the list.")
    print(f"Sample CNPJs: {cnpjs[:5]}")
    
    # 2. Analyze CSV structure
    files = sorted([f for f in os.listdir(cda_dir) if f.endswith(".csv")])
    for f in files:
        print(f"\n--- Analyzing {f} ---")
        file_path = os.path.join(cda_dir, f)
        # Read a few lines to see the header and content
        try:
            # Standard CVM files often use ISO-8859-1 and semicolon
            df_sample = pd.read_csv(file_path, sep=';', encoding='iso-8859-1', nrows=5)
            print(f"Columns: {df_sample.columns.tolist()}")
            print(f"Sample Data:\n{df_sample}")
        except Exception as e:
            print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    analyze_data()
