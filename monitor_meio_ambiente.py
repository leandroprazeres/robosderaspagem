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
            
            headline_text = None
            headline_link = None
            
            # Helper to extract link
            def extract_info(el):
                text = el.inner_text().strip()
                link = el.evaluate("node => { let a = node.closest('a'); return a ? a.href : (node.querySelector('a') ? node.querySelector('a').href : ''); }")
                return text, link

            try:
                page = context.new_page()
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
                
                for sel in selectors:
                    try:
                        page.wait_for_selector(sel, timeout=3000)
                        elements = page.locator(sel).all()
                        for el in elements:
                            text, link = extract_info(el)
                            if text and len(text) > 15:
                                headline_text = text
                                headline_link = link
                                break
                        if headline_text:
                            break
                    except Exception:
                        continue
                
                # Fallback
                if not headline_text:
                    for gen_sel in ["h1", "h2", "h3"]:
                        try:
                            elements = page.locator(gen_sel).all()
                            for el in elements:
                                text, link = extract_info(el)
                                if text and len(text) > 30:
                                    headline_text = text
                                    headline_link = link
                                    break
                            if headline_text:
                                break
                        except:
                            continue

                if headline_text:
                    resultados[name] = {"text": headline_text, "link": headline_link}
                else:
                    resultados[name] = {"text": "Manchete não identificada neste horário", "link": ""}
                page.close()
            except Exception as e:
                print(f"Erro ao acessar {name}: {e}")
                resultados[name] = {"text": "Falha ao carregar o portal", "link": ""}
                
        browser.close()
        return resultados

def send_email(headlines):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("ERRO: Credenciais de e-mail ausentes. Configuração do ambiente não encontrada.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Boletim de Manchetes: Meio Ambiente'
    
    content_text = "Aqui estão as principais manchetes de Meio Ambiente deste bloco:\n\n"
    content_html = "<html><body><p>Aqui estão as principais manchetes de Meio Ambiente deste bloco:</p><ul>"
    for portal, data in headlines.items():
        text = data.get("text", "")
        link = data.get("link", "")
        
        if link and not link.startswith("javascript"):
            content_text += f"🌲 {portal}: {text}\nLink: {link}\n\n"
            content_html += f"<li><b>{portal}</b>: <a href='{link}'>{text}</a></li>"
        else:
            content_text += f"🌲 {portal}: {text}\n\n"
            content_html += f"<li><b>{portal}</b>: {text}</li>"
            
    content_text += "--------------------------------------\nRobô ambiental concluído."
    content_html += "</ul><hr><p>Robô ambiental concluído.</p></body></html>"

    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content_text)
    msg.add_alternative(content_html, subtype='html')

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
            print(f"- {k}: {v['text']} ({v['link']})")
            
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
            print(f"{k}: {v['text']}\nLink: {v['link']}\n")
    else:
        main()
