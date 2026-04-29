import os
import email
from email import policy
from email.parser import BytesParser

export_dir = "/Users/prazel01/Downloads/Nova pasta 2/Relatório Indexado_03-03-2026/Exportados/arquivos"
output_dir = "/Users/prazel01/.gemini/antigravity/scratch/extracted_emails"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def extract_eml_to_txt(file_path, output_path):
    with open(file_path, 'rb') as fp:
        msg = BytesParser(policy=policy.default).parse(fp)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"From: {msg['from']}\n")
        f.write(f"To: {msg['to']}\n")
        f.write(f"Subject: {msg['subject']}\n")
        f.write(f"Date: {msg['date']}\n")
        f.write("-" * 50 + "\n\n")
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        
        f.write(body)

eml_files = []
for root, dirs, files in os.walk(export_dir):
    for file in files:
        if file.endswith(".eml"):
            eml_files.append(os.path.join(root, file))

for i, eml_path in enumerate(eml_files):
    output_filename = os.path.basename(eml_path).replace(".eml", ".txt")
    output_path = os.path.join(output_dir, output_filename)
    try:
        extract_eml_to_txt(eml_path, output_path)
        print(f"Processed: {output_filename}")
    except Exception as e:
        print(f"Error processing {eml_path}: {e}")

print(f"\nFinished processing {len(eml_files)} files.")
