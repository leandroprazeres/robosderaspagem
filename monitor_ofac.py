import os
import json
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
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
SCREENSHOT_FILE = "ofac_results.png"
OFAC_URL = 'https://sanctionssearch.ofac.treas.gov/'

def extract_brazil_entities_and_screenshot():
    """Navega no site da OFAC, seleciona Brazil, tira o screenshot e extrai a tabela."""
    print("Conectando ao banco de dados da OFAC via Playwright...")
    entities = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Carregar a página
            page.goto(OFAC_URL, timeout=30000)

            # 2. Selecionar o país
            page.select_option("#ctl00_MainContent_ddlCountry", label="Brazil")
            
            # 3. Clicar em Search e aguardar resultados
            page.click("#ctl00_MainContent_btnSearch")
            page.wait_for_selector("#gvSearchResults", timeout=15000)
            
            # 4. Tira o print screen (salva na máquina/runner)
            page.screenshot(path=SCREENSHOT_FILE, full_page=True)
            print(f"Print-screen da tela salvo com sucesso em {SCREENSHOT_FILE}")
            
            # 5. Extração dos dados da tabela
            rows = page.locator("#gvSearchResults tr").all()
            print(f"Foram encontrados {len(rows)} resultados.")
            
            for row in rows:
                cols = row.locator("td").all_inner_texts()
                if len(cols) >= 5:
                    entity = {
                        "Name": cols[0].strip(),
                        "Address": cols[1].strip(),
                        "Type": cols[2].strip(),
                        "Program": cols[3].strip(),
                        "List": cols[4].strip()
                    }
                    entities.append(entity)
                    
            browser.close()
        return entities
        
    except Exception as e:
        print(f"Erro durante a conexão/extração da OFAC: {e}")
        return None

def attach_screenshot(msg):
    """Anexa o print screen no e-mail, se existir."""
    if os.path.exists(SCREENSHOT_FILE):
        with open(SCREENSHOT_FILE, 'rb') as f:
            img_data = f.read()
        msg.add_attachment(img_data, maintype='image', subtype='png', filename='ofac_consulta.png')

def send_first_run_email(entities):
    """Envia o e-mail de Boas-vindas com a lista completa, confirmando que rodou uma vez."""
    msg = EmailMessage()
    msg['Subject'] = 'Bem-vindo: seu OFAC Robot está funcionando'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    body = f"Olá!\nO monitoramento da base de sanções da OFAC (EUA) para o BRASIL foi ativado com sucesso.\n\n"
    body += f"Como solicitado, este é o e-mail de boas-vindas. Esta execução encontrou {len(entities)} entidades do Brasil registradas:\n\n"
    body += "-"*50 + "\n"
    
    for e in entities:
        body += f"Nome: {e['Name']}\nEndereço: {e['Address']}\nTipo: {e['Type']}\nPrograma: {e['Program']}\nLista: {e['List']}\n"
        body += "-"*50 + "\n"
        
    body += "\nSegue também em anexo o print-screen da tela de consulta conforme solicitado."
    body += "\n(Você receberá um e-mail 'urgente' separado quando novos nomes surgirem nesta tabela no futuro)."
    
    msg.set_content(body)
    attach_screenshot(msg)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail de boas-vindas enviado!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail de boas-vindas: {e}")

def send_urgent_email(new_entities):
    """Envia um alerta urgente contendo os novos membros detectados."""
    msg = EmailMessage()
    msg['Subject'] = 'urgente - Nova organização brasileira na OFAC'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    body = "ATENÇÃO! Houve uma modificação na lista de entidades brasileiras na lista oficial da OFAC (EUA).\n\n"
    body += f"O seu robô detectou {len(new_entities)} nova(s) entidade(s):\n\n"
    
    for e in new_entities:
        body += f"> NOVO NOME INCLUÍDO: {e['Name']}\n"
        body += f"Endereço: {e['Address']}\nTipo: {e['Type']}\nPrograma: {e['Program']}\nLista: {e['List']}\n"
        body += "-"*50 + "\n"
        
    body += f"\nConsulta oficial: {OFAC_URL}\n"
    body += "Segue em anexo o print-screen da tela da atual consulta, como registro."
    
    msg.set_content(body)
    attach_screenshot(msg)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"E-mail de ALERTA URGENTE enviado com {len(new_entities)} novas entidades!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail urgente: {e}")

def send_no_changes_email(entities_count):
    """Envia um boletim informando que o monitor rodou e não há mudanças. OPCIONAL."""
    msg = EmailMessage()
    msg['Subject'] = 'OFAC Robot - Verificação Atual - Sem Mudanças'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    body = f"A verificação mais recente acabou de terminar.\n"
    body += f"Informamos que NÃO houve mudanças na lista de entidades brasileiras da OFAC desde a nossa última checagem.\n"
    body += f"A lista se mantém com {entities_count} entidade(s).\n\n"
    body += "Anexo o print da tela de consulta para controle."
    
    msg.set_content(body)
    attach_screenshot(msg)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail confirmando q não há mudanças foi enviado.")
    except Exception as e:
        print(f"Erro ao enviar o e-mail normal: {e}")

def get_new_entities(current_list, saved_list):
    """Compara as listas e retorna apenas o que tem na current e não tem na saved."""
    saved_names = {ent["Name"] for ent in saved_list}
    new_ones = []
    for ent in current_list:
        if ent["Name"] not in saved_names:
            new_ones.append(ent)
    return new_ones

def main():
    # Para forçar primeira execução, eu vou ignorar o JSON se ele existir, 
    # ou o usuário pode já ter apagado. Mas a lógica original cuidaria disso,
    # então usarei o estado local do arquivo mas adicionaremos um tratamento pra mandar print.
    current_entities = extract_brazil_entities_and_screenshot()
    
    if current_entities is None:
        print("Busca retornou vazia ou falhou. Abortando execução desta rodada.")
        return

    novidades = []
    first_run = False
    
    if os.path.exists(STATE_FILE):
        print("Lendo a memória local (estado anterior)...")
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            try:
                saved_entities = json.load(f)
            except json.JSONDecodeError:
                print("Arquivo de estado corrompido, considerando como primeira execução.")
                saved_entities = []
                
        if len(saved_entities) == 0:
            first_run = True
        else:
            novidades = get_new_entities(current_entities, saved_entities)
    else:
        first_run = True

    if first_run:
        print("Primeira execução detectada. Enviando Boas-Vindas e populando base.")
        send_first_run_email(current_entities)
    else:
        if novidades:
            print(f"DIFERENÇA DETECTADA! {len(novidades)} nova(s) entidade(s) brasileiras.")
            send_urgent_email(novidades)
        else:
            print("Nenhuma entidade nova encontrada. Informando sobre consulta sem mudanças.")
            # A pedido do usuário: "informe se houve mudanças" - vou enviar email para o usuario dizendo que nao houve
            # O cliente pediu pra avisar que testou hoje.
            send_no_changes_email(len(current_entities))

    # Atualiza base de dados
    print("Atualizando o arquivo de estado JSON localmente (e no GitHub logo após pelo git config)...")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_entities, f, ensure_ascii=False, indent=2)
    print("Concluído.")

if __name__ == "__main__":
    main()
