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
    print("ERRO: Credenciais de e-mail ausentes. Verifique as variáveis de ambiente no GitHub Secrets.")
    sys.exit(1)

# Arquivo local para armazenar a última organização terrorista registrada
STATE_FILE = "estado_fto.txt"

def get_latest_fto():
    """Acessa a página do Departamento de Estado e extrai a OTE (FTO) mais recente da tabela."""
    url = 'https://www.state.gov/foreign-terrorist-organizations/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O site geralmente possui a tabela de FTOs na primeira <table>.
        # A primeira linha <tr> é o cabeçalho (Date Designated / Name).
        # A segunda linha <tr> é a mais recente (pois está ordenada da mais nova pra mais antiga).
        table = soup.find('table')
        if not table:
            print("Tabela não encontrada na página.")
            return None
            
        rows = table.find_all('tr')
        if len(rows) < 2:
            print("Tabela vazia ou com formato inesperado.")
            return None
            
        # Pega a primeira linha de dados reais (ignorando o cabeçalho <th>)
        latest_row = rows[1]
        columns = latest_row.find_all(['td', 'th'])
        
        if len(columns) >= 2:
            date_designated = columns[0].get_text(strip=True)
            fto_name = columns[1].get_text(strip=True)
            
            # Limpa qualquer sobra de \n ou tags quebradas no meio do texto
            date_designated = " ".join(date_designated.split())
            fto_name = " ".join(fto_name.split())
            
            return fto_name, date_designated
            
        return None
    except Exception as e:
        print(f"Erro ao acessar Departamento de Estado: {e}")
        return None

def send_email(fto_name, date_designated, is_initial_run=False):
    """Envia o e-mail de alerta sobre a organização terrorista."""
    msg = EmailMessage()
    
    if is_initial_run:
        msg['Subject'] = 'BOAS-VINDAS: Monitor de FTOs Iniciado'
        content = f"""O monitoramento da Lista de Organizações Terroristas Estrangeiras do Departamento de Estado (EUA) foi ativado com sucesso.

A **última** entidade adicionada na lista até o momento é:
Organização: {fto_name}
Data de Inclusão: {date_designated}

Fonte: https://www.state.gov/foreign-terrorist-organizations/

Você receberá novos alertas caso uma entidade diferente seja incluída no topo da lista."""
    else:
        msg['Subject'] = 'ALERTA TERRORISMO: Nova Organização Adicionada (EUA)'
        content = f"""Atenção! Uma nova organização foi incluída na lista de FTOs do Departamento de Estado Norte-Americano.

Nova Organização TERRORISTA: {fto_name}
Data Oficial de Inclusão: {date_designated}

Acesse a lista oficial: https://www.state.gov/foreign-terrorist-organizations/

(Este é um alerta automático gerado pelo seu script de monitoramento)."""

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        print("E-mail de alerta enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")

def main():
    print("Verificando a lista de FTOs dos EUA...")
    result = get_latest_fto()
    
    if not result:
        print("Não foi possível encontrar a FTO atual na página.")
        return

    current_fto, current_date = result
    print(f"Entidade mais recente identificada: '{current_fto}' (Data: {current_date})")

    # Recupera a última entidade que foi vista pelo script
    previous_fto = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_fto = f.read().strip()

    # Compara a nova organização do topo da tabela com a que estava lá antes
    if current_fto != previous_fto:
        if previous_fto: # Só é alerta de NOVIDADE se já tiver uma salva antes
            print("NOVA ENTIDADE ENCONTRADA! Preparando para enviar e-mail.")
            send_email(current_fto, current_date, is_initial_run=False)
        else:
            print("Primeira execução registrada. Enviando e-mail de Boas-vindas.")
            send_email(current_fto, current_date, is_initial_run=True)
            
        # Atualiza o arquivo de estado com a FTO
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current_fto)
    else:
        print("A última entidade continua sendo a mesma. Nenhuma notificação enviada.")

if __name__ == "__main__":
    main()
