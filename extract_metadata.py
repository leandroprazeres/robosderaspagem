import pandas as pd
import requests
import io
import re
from PyPDF2 import PdfReader

def extract_metadata():
    file_path = '/Users/prazel01/Downloads/PLP 152 Outros documentos.xlsx'
    output_path = '/Users/prazel01/Downloads/PLP 152_Metadados_PDF.xlsx'

    print(f"Loading Excel file: {file_path}")
    df = pd.read_excel(file_path)

    results = []

    for index, row in df.iterrows():
        # The main link column is 'rightIconified href'
        link = row.get('rightIconified href')
        if pd.isna(link) or not isinstance(link, str) or not link.startswith('http'):
            continue
        
        # 'liTabelaTramitacoes' contains text with presenter context
        text = str(row.get('liTabelaTramitacoes', ''))
        
        # Try to find the presenter (e.g., "pelo Deputado Luiz Gastão")
        presenter_match = re.search(r'(?:pelo|pela)?\s*(Deputad[oa]\s+[^(,]+)', text, re.IGNORECASE)
        if presenter_match:
            presenter = presenter_match.group(1).strip()
        else:
            presenter = "Not found"
        
        print(f"Processing link: {link}")
        
        try:
            # Add User-Agent to avoid potential blocks
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(link, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Use PyPDF2 to read metadata
            pdf = PdfReader(io.BytesIO(response.content))
            meta = pdf.metadata
            
            if meta:
                metadata = {
                    'Link': link,
                    'Presenter': presenter,
                    'Context': text,
                    'Title': meta.title,
                    'Author': meta.author,
                    'Creator': meta.creator,
                    'Producer': meta.producer,
                    'Subject': meta.subject,
                    'CreationDate': meta.creation_date,
                    'ModDate': meta.modification_date,
                }
            else:
                metadata = {
                    'Link': link,
                    'Presenter': presenter,
                    'Context': text,
                    'Error': 'No metadata found'
                }
            
            results.append(metadata)
            
        except Exception as e:
            print(f"Error processing {link}: {e}")
            results.append({
                'Link': link,
                'Presenter': presenter,
                'Context': text,
                'Error': str(e)
            })

    print(f"Saving {len(results)} results to Excel...")
    out_df = pd.DataFrame(results)
    # Convert all columns to string to prevent Excel timezone errors
    for col in out_df.columns:
        # replace NaNs with empty string
        out_df[col] = out_df[col].apply(lambda x: '' if pd.isna(x) else str(x))
    out_df.to_excel(output_path, index=False)
    print(f"Extraction complete. Saved to {output_path}")

if __name__ == "__main__":
    extract_metadata()
