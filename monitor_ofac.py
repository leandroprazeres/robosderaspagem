import os
import json
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
import sys

# ==========================================
# CONFIGURAÇÕES DE E-MAIL (via Variáveis de Ambiente)
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    print("ERRO: Credenciais de e-mail ausentes. Verifique as variáveis de ambiente no GitHub Secrets.")
    sys.exit(1)

# Arquivo local para armazenar a lista completa de brasileiros na OFAC
STATE_FILE = "estado_ofac.json"
OFAC_URL = 'https://sanctionssearch.ofac.treas.gov/'

def extract_brazil_entities():
    """Navega no site da OFAC e retorna uma lista de dicionários com todos os resultados para 'Brazil'."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    session = requests.Session()
    print("Conectando ao banco de dados da OFAC...")
    
    try:
        # 1. Carregar a página inicial para pegar os tokens de segurança do ASP.NET
        r = session.get(OFAC_URL, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        view_state = soup.find('input', id='__VIEWSTATE')['value']
        view_state_gen = soup.find('input', id='__VIEWSTATEGENERATOR')['value']

        # 2. Localizar o código exato que o site usa para 'Brazil' no select box
        country_select = soup.find('select', id='ctl00_MainContent_ddlCountry')
        brazil_val = None
        if country_select:
            for opt in country_select.find_all('option'):
                if 'Brazil' in opt.text:
                    brazil_val = opt['value']
                    break
        
        if not brazil_val:
            print("Não foi possível encontrar a opção 'Brazil' no formulário.")
            return None

        # 3. Montar os dados de submissão do formulário simulando o clique em "Search"
        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_gen,
            'ctl00$MainContent$txtLastName': '',
            'ctl00$MainContent$txtIdNumber': '',
            'ctl00$MainContent$ddlType': '0', # All
            'ctl00$MainContent$ddlProgram': '0', # All
            'ctl00$MainContent$ddlList': '0', # All
            'ctl00$MainContent$txtMinimumNameScore': '100',
            'ctl00$MainContent$txtAddress': '',
            'ctl00$MainContent$txtCity': '',
            'ctl00$MainContent$txtState': '',
            'ctl00$MainContent$txtZip': '',
            'ctl00$MainContent$ddlCountry': brazil_val,
            'ctl00$MainContent$btnSearch': 'Search',
        }
        
        print("Executando a busca por entidades brasileiras...")
        r_post = session.post(OFAC_URL, data=data, headers=headers, timeout=30)
        r_post.raise_for_status()
        soup_post = BeautifulSoup(r_post.text, 'html.parser')
        
        table = soup_post.find('table', id='gvSearchResults')
        if not table:
            # Se não tiver tabela, pode ser que não haja nenhum resultado
            print("Nenhum resultado encontrado ou erro na tabela.")
            return []
            
        rows = table.find_all('tr')
        if not rows:
            return []
            
        print(f"Foram encontrados {len(rows)} resultados.")
        
        entities = []
        # A tabela de resultados gvSearchResults NÃO contém header no primeiro TR, todos são dados reais!
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cols) >= 5:
                # O formato da OFAC costuma ser: [Name, Address, Type, Programs, List, Score]
                entity = {
                    "Name": cols[0],
                    "Address": cols[1],
                    "Type": cols[2],
                    "Program": cols[3],
                    "List": cols[4]
                }
                entities.append(entity)
                
        return entities
        
    except Exception as e:
        print(f"Erro durante a conexão/extração da OFAC: {e}")
        return None

def send_first_run_email(entities):
    """Envia o e-mail de Boas-vindas com a lista completa."""
    msg = EmailMessage()
    msg['Subject'] = 'Bem-vindo: seu OFAC Robot está funcionando'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    body = f"Olá!\nO monitoramento da base de sanções da OFAC (EUA) para o BRASIL foi ativado com sucesso.\n\nAbaixo, a lista técnica atual com os {len(entities)} integrantes brasileiros já registrados:\n\n"
    body += "-"*50 + "\n"
    
    for e in entities:
        body += f"Nome: {e['Name']}\nEndereço: {e['Address']}\nTipo: {e['Type']}\nPrograma: {e['Program']}\nLista: {e['List']}\n"
        body += "-"*50 + "\n"
        
    body += "\n(Você receberá um e-mail 'urgente' separado apenas caso nomes novos surjam nesta tabela no futuro)."
    
    msg.set_content(body)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail de boas-vindas enviado!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail de boas-vindas: {e}")

def send_urgent_email(new_entities):
    """Envia um alerta urgente contendo apenas os novos membros detectados."""
    msg = EmailMessage()
    msg['Subject'] = 'urgente - Nova organizaçào brasileira na OFAC'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    body = "ATENÇÃO! O seu robô detectou novas inclusões na lista de sanções internacionais da OFAC (EUA).\n\n"
    body += f"Total de novas entidades encontradas nesta leitura: {len(new_entities)}\n\n"
    
    for e in new_entities:
        body += f"Nome: {e['Name']}\nEndereço: {e['Address']}\nTipo: {e['Type']}\nPrograma: {e['Program']}\nLista: {e['List']}\n"
        body += "-"*50 + "\n"
        
    body += f"\nConsulta oficial: {OFAC_URL}"
    
    msg.set_content(body)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"E-mail de ALERTA URGENTE enviado com {len(new_entities)} novas entidades!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail urgente: {e}")

def get_new_entities(current_list, saved_list):
    """Compara as listas e retorna apenas o que tem na current e não tem na saved."""
    # Transforma a lista salva numa lista apenas de nomes para facilitar a busca (ignorando mudanças pequenas no programa ou endereço)
    saved_names = {ent["Name"] for ent in saved_list}
    
    new_ones = []
    for ent in current_list:
        if ent["Name"] not in saved_names:
            new_ones.append(ent)
            
    return new_ones

def main():
    current_entities = extract_brazil_entities()
    
    if current_entities is None:
        print("Busca retornou vazia ou falhou. Abortando execução desta rodada.")
        return

    # Lê as informações antigas do disco (se existirem)
    if os.path.exists(STATE_FILE):
        print("Lendo a memória local (estado anterior)...")
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            try:
                saved_entities = json.load(f)
            except json.JSONDecodeError:
                print("Arquivo de estado corrompido, considerando como primeira execução.")
                saved_entities = []
                
        if len(saved_entities) == 0:
            print("Primeira execução (JSON vazio). Enviando as Boas-Vindas e populando.")
            send_first_run_email(current_entities)
        else:
            # Compara pra ver se há novas entidades
            novidades = get_new_entities(current_entities, saved_entities)
            if novidades:
                print(f"DIFERENÇA DETECTADA! {len(novidades)} nova(s) entidade(s) brasileiras.")
                send_urgent_email(novidades)
            else:
                print("Nenhuma entidade nova encontrada. Situação normal.")
    else:
        # Primeira Execução: arquivo nem existe
        print("Primeira execução. Salvando estado inicial e enviando e-mail de Boas-Vindas...")
        send_first_run_email(current_entities)

    # Sempre reescreve o arquivo JSON garantindo que esteja atualizado no fim da rodada
    print("Atualizando o arquivo de estado JSON...")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_entities, f, ensure_ascii=False, indent=2)
    print("Concluído.")

if __name__ == "__main__":
    main()
