import os
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
    print("ERRO: Credenciais de e-mail ausentes. Verifique as variáveis de ambiente.")
    sys.exit(1)

# Arquivo local para armazenar a última manchete registrada
STATE_FILE = "ultima_manchete_uol.txt"

def get_main_headline():
    """Acessa a página principal do UOL e extrai a manchete principal."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get('https://www.uol.com.br/', headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # No UOL, a manchete principal geralmente possui a classe 'headlineMain__title'
        main_title_tag = soup.find(class_='headlineMain__title')
        if main_title_tag:
            return main_title_tag.get_text(strip=True)
            
        # Fallback de segurança: pegar o primeiro <h3> (que costumam ser os títulos maiores)
        h3 = soup.find('h3', class_='title__element')
        if h3:
            return h3.get_text(strip=True)
            
        return None
    except Exception as e:
        print(f"Erro ao acessar UOL: {e}")
        return None

def send_email(new_headline, mudou=True):
    """Envia o e-mail de alerta com a nova manchete."""
    msg = EmailMessage()
    
    if mudou:
        msg['Subject'] = 'ALERTA: Nova Manchete Principal no UOL'
        content = f"A manchete principal do UOL acaba de mudar!\n\nNova manchete:\n'{new_headline}'\n\nAcesse agora: https://www.uol.com.br/\n\n(Este é um e-mail automático gerado pelo seu script de monitoramento)."
    else:
        msg['Subject'] = 'Iniciando Monitoramento do UOL'
        content = f"O monitoramento do UOL foi iniciado com sucesso!\n\nA manchete atual é:\n'{new_headline}'\n\nVocê receberá um novo e-mail quando ela mudar."

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content)
    
    try:
        # Configuração para Gmail usando SSL (porta 465)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        print("E-mail de alerta enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")
        print("Verifique suas credenciais e a configuração de 'Senhas de App' no Gmail.")

def main():
    print("Verificando a página do UOL...")
    current_headline = get_main_headline()
    
    if not current_headline:
        print("Não foi possível encontrar a manchete atual na página.")
        return

    print(f"Manchete atual identificada: '{current_headline}'")

    # Recupera a última manchete que foi vista pelo script
    previous_headline = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_headline = f.read().strip()

    # Compara a nova com a antiga
    if current_headline != previous_headline:
        if previous_headline: # Só avisa se não for a primeira execução salva
            print("A manchete MUDOU! Preparando para enviar e-mail.")
            send_email(current_headline, mudou=True)
        else:
            print("Primeira execução registrada. Enviando e-mail de confirmação de funcionamento.")
            send_email(current_headline, mudou=False)
            
        # Atualiza o arquivo com a nova manchete
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current_headline)
    else:
        print("A manchete continua a mesma. Nenhuma notificação necessária.")

if __name__ == "__main__":
    main()
