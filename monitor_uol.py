import os
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

PORTALS = [
    {"name": "Folha", "url": "https://www.folha.uol.com.br/", "selectors": [".c-main-headline__title"]},
    {"name": "UOL", "url": "https://www.uol.com.br/", "selectors": [".xkZfD", ".headlineMain__title", "h2.title", "h3.title", "h2.thumb-title"]},
    {"name": "Estadão", "url": "https://www.estadao.com.br/", "selectors": [".headline", "h2.title"]},
    {"name": "O Globo", "url": "https://oglobo.globo.com/", "selectors": [".materia-chamada__titulo"]},
    {"name": "Metrópoles", "url": "https://www.metropoles.com/", "selectors": [".m-title-headline", ".m-title"]},
    {"name": "NYT", "url": "https://www.nytimes.com/", "selectors": ["[data-testid='block-TopStory'] h3", "[data-testid='block-TopStory'] h1", "section.story-wrapper h1", ".indicate-hover"]},
    {"name": "Washington Post", "url": "https://www.washingtonpost.com/", "selectors": ["[data-qa='headline']", "[data-pb-local-id='headline']", ".font--headline"]},
    {"name": "Le Monde", "url": "https://www.lemonde.fr/", "selectors": [".article__title"]},
    {"name": "Le Figaro", "url": "https://www.lefigaro.fr/", "selectors": [".fig-main-profile__title", ".fig-profile__headline"]},
    {"name": "BBC UK", "url": "https://www.bbc.co.uk", "selectors": ["[data-testid='edgel-headline']", "[data-testid='card-headline']", "h3"]},
    {"name": "BBC Brasil", "url": "https://www.bbc.com/portuguese", "selectors": ["h3"]}
]

def get_headlines():
    """Acessa as páginas usando Playwright e extrai a manchete principal decrescendo rigor sobre seletores."""
    resultados = {}
    print("Iniciando navegador headless para acessar os portais...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        for portal in PORTALS:
            name = portal["name"]
            url = portal["url"]
            selectors = portal["selectors"]
            print(f"[{name}] Acessando {url} ...")
            
            headline = None
            try:
                page = context.new_page()
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
                
                # Tenta cada seletor na ordem (para priorizar título da matéria ao invés do H1 da logo)
                for sel in selectors:
                    try:
                        # Espera rápida para o seletor existir
                        page.wait_for_selector(sel, timeout=3000)
                        # Pega todos os matches e pega o primeiro que tiver texto razoável
                        elements = page.locator(sel).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            if text and len(text) > 10:
                                headline = text
                                break
                        if headline:
                            break # Achou uma manchete viável com esse seletor
                    except Exception:
                        continue # tenta o próximo seletor
                
                # Fallback genérico caso todos falhem e ele tenha carregado
                if not headline:
                    for gen_sel in ["h1", "h2"]:
                        try:
                            elements = page.locator(gen_sel).all()
                            for el in elements:
                                text = el.inner_text().strip()
                                # Evita pegar logos que costumam ter texto curto (ex: "oglobo", "Metrópoles")
                                if text and len(text) > 25:
                                    headline = text
                                    break
                            if headline:
                                break
                        except:
                            continue

                resultados[name] = headline if headline else "Manchete não identificada neste horário"
                page.close()
            except Exception as e:
                print(f"Erro ao acessar {name}: {e}")
                resultados[name] = "Falha ao carregar o portal"
                
        browser.close()
        return resultados


def send_email(headlines):
    """Envia o e-mail de alerta apenas com as manchetes finais."""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("ERRO: Credenciais de e-mail ausentes. Configuração do ambiente não encontrada.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Boletim de Manchetes Principais'
    
    content = "Aqui estão as principais manchetes deste horário:\n\n"
    for portal, headline in headlines.items():
        content += f"➡️ {portal}: {headline}\n\n"
        
    content += "--------------------------------------\n"
    content += "Robô de raspagem concluído com sucesso."

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("\nE-mail de boletim enviado com sucesso!")
    except Exception as e:
        print(f"\nErro ao enviar o e-mail: {e}")
        import traceback
        with open("email_error.txt", "w", encoding="utf-8") as err_f:
            err_f.write(f"Erro: {e}\n\n{traceback.format_exc()}")


def main():
    print("Iniciando varredura profunda nas manchetes...")
    current_headlines = get_headlines()
    
    # Diferente do antigo comportamento, nós apenas formatamos as manchetes e enviamos. 
    # Não gravamos estado (old vs new), cumprindo a regra de envio no horário cravado.
    if current_headlines:
        print("\nManchetes coletadas:")
        for k, v in current_headlines.items():
            print(f"- {k}: {v}")
            
        print("\nIniciando envio de e-mail...")
        send_email(current_headlines)
    else:
        print("Nenhuma manchete coletada no processo.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Apenas raspa e mostra no console sem enviar e-mail.")
    args = parser.parse_args()

    if args.test:
        print("MODO DE TESTE ATIVADO: Não enviaremos e-mail.")
        headlines = get_headlines()
        print("\n--- RESULTADOS DO TESTE ---")
        for k, v in headlines.items():
            print(f"{k}: {v}")
    else:
        main()
