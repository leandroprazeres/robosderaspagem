import os
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from datetime import datetime
import time

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

URLS = {
    "GE.globo.com": {
        "url": "https://ge.globo.com/",
        "selectors": [".feed-post-link"]
    },
    "Marca - Barcelona": {
        "url": "https://www.marca.com/futbol/barcelona.html",
        "selectors": [".ue-c-cover-content__headline-group h2"]
    },
    "Marca - Real Madrid": {
        "url": "https://www.marca.com/futbol/real-madrid.html",
        "selectors": [".ue-c-cover-content__headline-group h2"]
    },
    "Marca - Atletico": {
        "url": "https://www.marca.com/futbol/atletico.html",
        "selectors": [".ue-c-cover-content__headline-group h2"]
    },
    "Marca - Liverpool": {
        "url": "https://www.marca.com/organizacion/liverpool.html",
        "selectors": [".ue-c-cover-content__headline-group h2"]
    },
    "Marca - Futebol": {
        "url": "https://www.marca.com/futbol.html",
        "selectors": [".ue-c-cover-content__headline-group h2"]
    },
    "Lance - Fluminense": {
        "url": "https://www.lance.com.br/fluminense",
        "selectors": [".title-feed"]
    }
}


def get_headlines():
    print("Iniciando coleta de manchetes...")
    headlines = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for site_name, config in URLS.items():
            print(f"Acessando {site_name}")
            try:
                context = browser.new_context()
                page = context.new_page()
                page.goto(config["url"], timeout=45000, wait_until="domcontentloaded")

                for sel in config["selectors"]:
                    try:
                        page.wait_for_selector(sel, timeout=3000)
                        elements = page.locator(sel).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            link = el.get_attribute("href")
                            if text and link:
                                headlines.append({"site": site_name, "text": text, "link": link})
                                break
                    except Exception as e:
                        print(f"Erro ao coletar manchetes de {site_name}: {e}")

            except Exception as e:
                print(f"Erro ao acessar {config['url']}: {e}")

        browser.close()
    return headlines


def send_email(headlines):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        print("ERRO: Credenciais de e-mail ausentes. O e-mail não será enviado.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Manchetes do Dia - Resumo Esportivo'

    content_text = "Bom dia! Veja aqui as principais manchetes que selecionei para você:\n\n"
    content_html = """
    <html>
      <body>
        <p>Bom dia! Veja aqui as principais manchetes que selecionei para você:</p>
        <ul>
    """

    for headline in headlines:
        content_text += f"- {headline['site']}: {headline['text']} ({headline['link']})\n"
        content_html += f"<li><strong>{headline['site']}</strong>: <a href='{headline['link']}'>{headline['text']}</a></li>"

    content_html += "</ul></body></html>"

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content_text)
    msg.add_alternative(content_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")


def main():
    print("Iniciando execução do monitor...")
    while True:
        now = datetime.now()
        if now.hour in [6, 12, 18, 0] and now.minute == 0:
            headlines = get_headlines()
            if headlines:
                send_email(headlines)
            else:
                print("Nenhuma manchete foi coletada.")
            time.sleep(60)  # Evita múltiplas execuções no mesmo minuto
        time.sleep(30)  # Verifica a cada 30 segundos


if __name__ == "__main__":
    main()