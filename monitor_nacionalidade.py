import os
import smtplib
import time
import random
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
import sys

# ==========================================
# CONFIGURAÇÕES (via Variáveis de Ambiente)
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
PROCESS_NUMBER = "6616-5131-7824"  # Número do processo formatado

if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    print("ERRO: Credenciais de e-mail ausentes.")
    sys.exit(1)

STATE_FILE = "estado_nacionalidade.txt"
SCREENSHOT_FILE = "nacionalidade_resultado.png"
TARGET_URL = "https://meu.registo.justica.gov.pt/Pedidos/Consultar-estado-do-processo-de-nacionalidade"

def human_delay(min_ms=500, max_ms=1500):
    """Aguarda um tempo aleatório para simular comportamento humano."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

def get_process_status():
    """Abre o site, preenche o formulário, tenta resolver o hCaptcha e retorna o status."""
    print("Iniciando navegador headless com perfil furtivo...")

    try:
        with sync_playwright() as p:
            # Usar um contexto semelhante ao de um usuário real
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="pt-PT",
                timezone_id="Europe/Lisbon",
                # Simular que o navegador aceita cookies e scripts normais
                java_script_enabled=True,
            )
            
            # Remover identificação de webdriver
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['pt-PT', 'pt', 'en-US']});
                window.chrome = { runtime: {} };
            """)

            page = context.new_page()

            # Carregar a página
            print(f"Acessando: {TARGET_URL}")
            try:
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
                print("Página carregada (DOM Content Loaded). Aguardando rede estabilizar...")
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                print(f"Aviso durante carregamento inicial: {e}")
                print("Tentando prosseguir com o que carregou...")
            
            human_delay(2000, 4000)

            # Preencher o campo de senha de acesso
            print(f"Preenchendo o número do processo: {PROCESS_NUMBER}")
            input_field = page.locator("#Input_TextVar")
            input_field.click()
            human_delay(300, 700)
            input_field.fill(PROCESS_NUMBER)
            human_delay(500, 1000)

            # Tentar clicar no checkbox do hCaptcha
            print("Tentando clicar no checkbox do hCaptcha...")
            try:
                # hCaptcha fica dentro de um iframe
                hcaptcha_frame = page.frame_locator("iframe[src*='hcaptcha']")
                checkbox = hcaptcha_frame.locator("#checkbox")
                checkbox.click(timeout=5000)
                human_delay(2000, 4000)
                print("Checkbox clicado. Aguardando validação do hCaptcha...")
            except Exception as e:
                print(f"Aviso: Não foi possível clicar no checkbox do hCaptcha: {e}")
                print("Tentando prosseguir mesmo assim...")

            # Clicar em Pesquisar
            print("Clicando em 'Pesquisar'...")
            page.locator("button.btn-primary", has_text="Pesquisar").click()
            human_delay(3000, 5000)

            # Aguardar resultado (página deve recarregar ou mostrar resultado)
            page.wait_for_load_state("networkidle", timeout=15000)
            human_delay(1000, 2000)

            # Tirar screenshot do resultado
            page.screenshot(path=SCREENSHOT_FILE, full_page=True)
            print(f"Screenshot salvo: {SCREENSHOT_FILE}")

            # Extrair o texto do resultado da página
            # O status costuma aparecer em um elemento de texto principal
            page_text = page.locator("body").inner_text()
            
            # Tentar encontrar o bloco de resultado específico
            status_text = ""
            try:
                # Tenta pegar o elemento de resultado se existir
                result_block = page.locator(".feedback-message, .alert, .result, [class*='estado'], [class*='status'], h2, h3, p")
                texts = result_block.all_inner_texts()
                status_text = "\n".join([t.strip() for t in texts if t.strip() and len(t.strip()) > 5])
            except Exception:
                pass
            
            if not status_text:
                status_text = page_text[:2000]  # Fallback: primeiros 2000 chars da página

            browser.close()
            return status_text.strip()

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        return None

def send_email(status_text, changed=False, is_first_run=False):
    """Envia o e-mail com o status do processo."""
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    if is_first_run:
        msg["Subject"] = "Monitor Ativo: Estado do Processo de Nacionalidade Portuguesa"
        intro = (
            "O monitoramento diário do seu processo de nacionalidade portuguesa foi ativado!\n\n"
            "Você receberá um e-mail toda manhã às 7h com o status do processo.\n\n"
            "== STATUS ATUAL ==\n"
        )
    elif changed:
        msg["Subject"] = "🚨 ALERTA: Mudança no Processo de Nacionalidade Portuguesa!"
        intro = (
            "ATENÇÃO! Detectamos uma mudança no estado do seu processo de nacionalidade!\n\n"
            "== NOVO STATUS ==\n"
        )
    else:
        msg["Subject"] = "Relatório Diário: Processo de Nacionalidade Portuguesa"
        intro = (
            f"Bom dia! Aqui está a atualização diária do seu processo de nacionalidade.\n\n"
            f"Processo nº: {PROCESS_NUMBER}\n\n"
            "== STATUS ATUAL ==\n"
        )

    body = intro + status_text + f"\n\n---\nConsulta realizada via: {TARGET_URL}"
    msg.set_content(body)

    # Anexar screenshot se existir
    if os.path.exists(SCREENSHOT_FILE):
        with open(SCREENSHOT_FILE, "rb") as f:
            img_data = f.read()
        msg.add_attachment(img_data, maintype="image", subtype="png", filename="resultado_nacionalidade.png")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def main():
    print(f"Iniciando verificação do processo: {PROCESS_NUMBER}")
    
    current_status = get_process_status()

    if not current_status:
        print("Não foi possível obter o status. O hCaptcha pode ter bloqueado o acesso.")
        # Enviar e-mail de aviso mesmo assim
        msg = EmailMessage()
        msg["Subject"] = "Aviso: Monitor de Nacionalidade não conseguiu acessar o site"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg.set_content(
            "O robô tentou verificar seu processo de nacionalidade, mas o site bloqueou o acesso "
            "(provável bloqueio de hCaptcha). Tente acessar manualmente:\n\n"
            f"{TARGET_URL}"
        )
        # Attach screenshot if we have one (even if partial)
        if os.path.exists(SCREENSHOT_FILE):
            with open(SCREENSHOT_FILE, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="png", filename="bloqueio.png")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
        except Exception as e:
            print(f"Erro ao enviar e-mail de aviso: {e}")
        return

    print(f"Status obtido:\n{current_status[:500]}...")

    # Comparar com estado anterior
    previous_status = ""
    is_first_run = False

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_status = f.read().strip()
    else:
        is_first_run = True

    changed = (current_status != previous_status) and not is_first_run

    if changed:
        print("STATUS MUDOU! Enviando alerta urgente.")
    elif is_first_run:
        print("Primeira execução. Enviando e-mail de boas-vindas.")
    else:
        print("Status igual ao anterior. Enviando relatório diário.")

    send_email(current_status, changed=changed, is_first_run=is_first_run)

    # Salvar estado atual
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(current_status)
    print("Estado salvo. Concluído.")

if __name__ == "__main__":
    main()
