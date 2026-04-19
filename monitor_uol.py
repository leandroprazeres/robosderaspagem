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

# Arquivo JSON local para armazenar as manchetes
STATE_FILE = "ultimas_manchetes.json"

PORTALS = [
    {"name": "Folha", "url": "https://www.folha.uol.com.br/", "selector": ".c-main-headline__title"},
    {"name": "UOL", "url": "https://www.uol.com.br/", "selector": ".xkZfD, h2.title, h3.title, .headlineMain__title, h2.thumb-title, h1"},
    {"name": "Estadão", "url": "https://www.estadao.com.br/", "selector": ".headline, h2.title, h1"},
    {"name": "O Globo", "url": "https://oglobo.globo.com/", "selector": ".materia-chamada__titulo, h1"},
    {"name": "Metrópoles", "url": "https://www.metropoles.com/", "selector": ".m-title, .m-title-headline, h1"},
    {"name": "NYT", "url": "https://www.nytimes.com/", "selector": "[data-testid='block-TopStory'] h1, [data-testid='block-TopStory'] h3, .indicate-hover, h1"},
    {"name": "Washington Post", "url": "https://www.washingtonpost.com/", "selector": "[data-qa='headline'], [data-pb-local-id='headline'], .font--headline, h2"},
    {"name": "Le Monde", "url": "https://www.lemonde.fr/", "selector": ".article__title, h1"},
    {"name": "Le Figaro", "url": "https://www.lefigaro.fr/", "selector": ".fig-main-profile__title, .fig-profile__headline, h1"},
    {"name": "BBC UK", "url": "https://www.bbc.co.uk", "selector": "[data-testid='edgel-headline'], h2[data-testid='card-headline'], h3"},
    {"name": "BBC Brasil", "url": "https://www.bbc.com/portuguese", "selector": "h3, h1"}
]

def get_headlines():
    """Acessa as páginas usando Playwright e extrai a manchete principal."""
    resultados = {}
    print("Iniciando navegador headless para acessar os portais...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            for portal in PORTALS:
                name = portal["name"]
                url = portal["url"]
                selector = portal["selector"]
                print(f"[{name}] Acessando {url} ...")
                
                try:
                    page = context.new_page()
                    # wait_until="domcontentloaded" is faster and less prone to timeout from ads
                    page.goto(url, timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_selector(selector, timeout=15000)
                    headline = page.locator(selector).first.inner_text()
                    if headline:
                        resultados[name] = headline.strip()
                    else:
                        resultados[name] = None
                    page.close()
                except Exception as e:
                    print(f"Erro ao acessar {name}: {e}")
                    resultados[name] = None
                    
            browser.close()
            return resultados
    except Exception as e:
        print(f"Erro ao iniciar o Playwright: {e}")
        return resultados

def send_email(changes, is_first_run=False):
    """Envia o e-mail de alerta com as novas manchetes."""
    msg = EmailMessage()
    
    if is_first_run:
        msg['Subject'] = 'Iniciando Monitoramento Multi-Portais'
        content = "O monitoramento dos portais de notícias foi iniciado com sucesso!\n\nManchetes atuais:\n\n"
        for portal, info in changes.items():
            content += f"- {portal}: '{info['new']}'\n"
        content += "\nVocê receberá um novo e-mail quando qualquer uma delas mudar."
    else:
        msg['Subject'] = 'ALERTA: Novas Manchetes Principais Detectadas'
        content = "As seguintes manchetes mudaram:\n\n"
        for portal, info in changes.items():
            content += f"[{portal}]\nAntes: '{info['old']}'\nAgora: '{info['new']}'\n\n"
        content += "\n(Este é um e-mail automático gerado pelo seu script de monitoramento)."

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail de alerta enviado com sucesso!")
        if os.path.exists("email_error.txt"):
            os.remove("email_error.txt")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")
        import traceback
        with open("email_error.txt", "w", encoding="utf-8") as err_f:
            err_f.write(f"Erro: {e}\n\n{traceback.format_exc()}")
        print("Verifique suas credenciais e a configuração de 'Senhas de App' no Gmail.")

def main():
    print("Iniciando verificação de portais...")
    current_headlines = get_headlines()
    
    if not current_headlines:
        print("Não foi possível coletar nenhuma manchete. (Erro geral)")
        return
        
    previous_headlines = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                previous_headlines = json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo de estado: {e}")
            previous_headlines = {}

    changes = {}
    valid_reads = 0
    
    for name, curr_text in current_headlines.items():
        if curr_text:
            valid_reads += 1
            prev_text = previous_headlines.get(name)
            
            # Atualiza no dicionário do estado atual
            previous_headlines[name] = curr_text
            
            if prev_text != curr_text:
                changes[name] = {"old": prev_text if prev_text else "N/A", "new": curr_text}

    if not previous_headlines:  # first run ever with json
        print("Primeira execução registrada. Preparando e-mail de boas-vindas com todas as manchetes...")
        for name, curr_text in current_headlines.items():
            if curr_text:
                changes[name] = {"old": "N/A", "new": curr_text}
        
        if changes:
            send_email(changes, is_first_run=True)
    elif changes:
        print(f"Mudanças detectadas em {len(changes)} portal/portais. Preparando e-mail...")
        send_email(changes, is_first_run=False)
    else:
        print(f"Leituras bem-sucedidas em {valid_reads} portais. Nenhuma mudança detectada na execução de agora.")

    # Always save state for successful items
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(previous_headlines, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
