import os
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
import sys

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "clarapresotti@gmail.com")

PORTALS = [
    {"name": "Folha (Ambiente)", "url": "https://www1.folha.uol.com.br/ambiente/", "selectors": [".c-headline__title", ".c-main-headline__title", "h2.c-headline__title"]},
    {"name": "O Globo (Meio Ambiente)", "url": "https://oglobo.globo.com/brasil/meio-ambiente/", "selectors": [".feed-post-link", ".materia-chamada__titulo", ".title"]},
    {"name": "G1 (Meio Ambiente)", "url": "https://g1.globo.com/meio-ambiente/", "selectors": [".feed-post-link", ".materia-chamada__titulo", ".title"]},
    {"name": "Mongabay Brasil", "url": "https://brasil.mongabay.com/", "selectors": [".article-title", ".post-title", ".headline", "h2.entry-title"]},
    {"name": "O Eco (Notícias)", "url": "https://oeco.org.br/category/noticias/", "selectors": [".entry-title", ".post-title", "h2.elementor-heading-title", "h3.elementor-heading-title"]}
]

def get_headlines():
    resultados = {}
    print("Iniciando navegador headless para acessar os portais de meio ambiente...")
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
                
                for sel in selectors:
                    try:
                        page.wait_for_selector(sel, timeout=3000)
                        elements = page.locator(sel).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            if text and len(text) > 15:
                                headline = text
                                break
                        if headline:
                            break
                    except Exception:
                        continue
                
                # Fallback
                if not headline:
                    for gen_sel in ["h1", "h2", "h3"]:
                        try:
                            elements = page.locator(gen_sel).all()
                            for el in elements:
                                text = el.inner_text().strip()
                                if text and len(text) > 30:
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
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("ERRO: Credenciais de e-mail ausentes. Configuração do ambiente não encontrada.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Boletim de Manchetes: Meio Ambiente'
    
    content = "Aqui estão as principais manchetes de Meio Ambiente deste bloco:\n\n"
    for portal, headline in headlines.items():
        content += f"🌲 {portal}: {headline}\n\n"
        
    content += "--------------------------------------\n"
    content += "Robô ambiental concluído."

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
        with open("email_error_ambiente.txt", "w", encoding="utf-8") as err_f:
            err_f.write(f"Erro: {e}\n\n{traceback.format_exc()}")

def main():
    print("Iniciando varredura em sites de Meio Ambiente...")
    current_headlines = get_headlines()
    
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
    parser.add_argument("--test", action="store_true", help="Apenas raspa e mostra no console.")
    args = parser.parse_args()

    if args.test:
        print("MODO DE TESTE ATIVADO: Não enviaremos e-mail.")
        headlines = get_headlines()
        print("\n--- RESULTADOS DO TESTE (MEIO AMBIENTE) ---")
        for k, v in headlines.items():
            print(f"{k}: {v}")
    else:
        main()
