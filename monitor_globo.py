import os
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = "leoonetybsb@gmail.com"

URL = "https://www.globo.com/"
SELECTORS = [
    ".hui-manchete__title", 
    ".hui-manchete__link", 
    ".post__title", 
    "h2.post__title"
]

def get_globo_headline():
    print("Iniciando navegador headless para acessar globo.com...")
    resultado = {"text": "Manchete não encontrada", "link": ""}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        try:
            page = context.new_page()
            page.goto(URL, timeout=45000, wait_until="domcontentloaded")
            
            headline_text = None
            headline_link = None
            
            def extract_info(el):
                text = el.inner_text().strip()
                link = el.evaluate("node => { let a = node.closest('a'); return a ? a.href : (node.querySelector('a') ? node.querySelector('a').href : ''); }")
                return text, link

            for sel in SELECTORS:
                try:
                    page.wait_for_selector(sel, timeout=3000)
                    elements = page.locator(sel).all()
                    for el in elements:
                        text, link = extract_info(el)
                        # Ignora textos muito curtos que podem não ser a manchete
                        if text and len(text) > 20: 
                            headline_text = text
                            headline_link = link
                            break
                    if headline_text:
                        break
                except Exception:
                    continue

            # Fallback
            if not headline_text:
                for gen_sel in ["h2"]:
                    try:
                        elements = page.locator(gen_sel).all()
                        for el in elements:
                            text, link = extract_info(el)
                            if text and len(text) > 40 and "globo" not in text.lower():
                                headline_text = text
                                headline_link = link
                                break
                        if headline_text:
                            break
                    except:
                        continue

            if headline_text:
                resultado = {"text": headline_text, "link": headline_link}
        except Exception as e:
            print(f"Erro ao acessar {URL}: {e}")
        finally:
            browser.close()
            
    return resultado

def send_email(headline):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        print("ERRO: Credenciais de e-mail ausentes. O e-mail não será enviado.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Manchete do Dia - globo.com'
    
    texto = headline.get("text", "")
    link = headline.get("link", "")
    
    content_text = f"Bom dia, meu filho amado. Veja aqui as manchetes que eu selecionei pra você!\nTe amo!\n\nManchete: {texto}\nLink: {link}\n"
    
    content_html = f"""
    <html>
      <body>
        <p>Bom dia, meu filho amado. Veja aqui as manchetes que eu selecionei pra você!</p>
        <p>Te amo!</p>
        <h2><a href='{link}'>{texto}</a></h2>
      </body>
    </html>
    """
    
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(content_text)
    msg.add_alternative(content_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("\nE-mail enviado com sucesso para Leonardo!")
    except Exception as e:
        print(f"\nErro ao enviar o e-mail: {e}")

def main():
    print("Iniciando coleta da manchete...")
    headline = get_globo_headline()
    print(f"\nManchete coletada:\n- {headline['text']}\n- Link: {headline['link']}")
    
    if headline["text"] != "Manchete não encontrada":
        if os.environ.get("TEST_RUN"):
            print("\nModo de teste: o e-mail não foi enviado.")
        else:
            print("\nIniciando envio de e-mail...")
            send_email(headline)
    else:
        print("Nenhuma manchete coletada para enviar.")

if __name__ == "__main__":
    main()
