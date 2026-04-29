import os
import smtplib
from email.message import EmailMessage
import datetime

# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# Lista de livros cobrados frequentemente nos grandes vestibulares (FUVEST, UNICAMP, etc.)
LIVROS = [
    {"titulo": "Dom Casmurro", "autor": "Machado de Assis", "resumo": "Um clássico sobre ciúme e a ambiguidade da traição. Fundamental para entender o Realismo brasileiro."},
    {"titulo": "Vidas Secas", "autor": "Graciliano Ramos", "resumo": "Retrato duro e emocionante de uma família de retirantes fugindo da seca no sertão nordestino."},
    {"titulo": "O Cortiço", "autor": "Aluísio Azevedo", "resumo": "A principal obra do Naturalismo brasileiro, mostrando como o ambiente e a convivência moldam e corrompem o comportamento humano."},
    {"titulo": "Quarto de Despejo", "autor": "Carolina Maria de Jesus", "resumo": "Diário real e cru de uma mulher negra e favelada que narra as dificuldades de sobreviver e alimentar os filhos."},
    {"titulo": "Mensagem", "autor": "Fernando Pessoa", "resumo": "Único livro em português publicado em vida pelo autor. É um poema épico que revisita e glorifica a história e os heróis de Portugal."},
    {"titulo": "A Relíquia", "autor": "Eça de Queirós", "resumo": "Sátira incisiva à hipocrisia religiosa e social da sociedade burguesa de Portugal do século XIX."},
    {"titulo": "Alguma Poesia", "autor": "Carlos Drummond de Andrade", "resumo": "Obra de estreia do autor, que introduz temas existenciais, amorosos e a visão irônica sobre a vida com uma linguagem inovadora."},
    {"titulo": "Romanceiro da Inconfidência", "autor": "Cecília Meireles", "resumo": "Obra épico-lírica que resgata as vozes e o sofrimento dos envolvidos na Inconfidência Mineira."},
    {"titulo": "Dois Irmãos", "autor": "Milton Hatoum", "resumo": "A história de conflito entre os irmãos gêmeos Yaqub e Omar, no contexto de uma família de imigrantes libaneses em Manaus."},
    {"titulo": "Capitães da Areia", "autor": "Jorge Amado", "resumo": "Conta a vida de um grupo de meninos de rua abandonados em Salvador, explorando denúncia social e lirismo."},
    {"titulo": "Mayombe", "autor": "Pepetela", "resumo": "Narrativa sobre a guerra de libertação de Angola contra a colonização portuguesa, mostrando as tensões e os ideais dos guerrilheiros."},
    {"titulo": "Marília de Dirceu", "autor": "Tomás Antônio Gonzaga", "resumo": "Obra basilar do Arcadismo no Brasil, dividida em poemas de amor da juventude e de sofrimento pelo exílio e prisão."},
    {"titulo": "A Cidade e as Serras", "autor": "Eça de Queirós", "resumo": "Romance que opõe a artificialidade e a vida atribulada na cidade grande (Paris) com a simplicidade e paz do campo."},
    {"titulo": "Angústia", "autor": "Graciliano Ramos", "resumo": "Mergulho psicológico profundo na mente de Luís da Silva, misturando seus delírios, medos do presente e memórias do passado nordestino."},
    {"titulo": "Nove Noites", "autor": "Bernardo Carvalho", "resumo": "Romance contemporâneo investigativo sobre o suicídio de um antropólogo americano numa tribo indígena no Brasil."}
]

def get_book_of_the_week():
    # Usa o número da semana do ano para selecionar um livro (rotação contínua)
    week_number = datetime.date.today().isocalendar()[1]
    index = week_number % len(LIVROS)
    return LIVROS[index]

def send_email(livro):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD]):
        print("ERRO: Credenciais de e-mail ausentes. O e-mail não será enviado.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Dica de Leitura para o Vestibular 📚'
    
    content_text = f"Bom dia, meu filho amado!\n\nPara a sua preparação do vestibular essa semana, separei esta sugestão de leitura muito importante:\n\n📖 Livro: {livro['titulo']}\n✍️ Autor: {livro['autor']}\n💡 Sobre a obra: {livro['resumo']}\n\nFoque nos estudos! Te amo!"
    
    content_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Bom dia, meu filho amado!</p>
        <p>Para a sua preparação do vestibular essa semana, separei esta sugestão de leitura que sempre marca presença nas provas (FUVEST/Unicamp):</p>
        <div style="background-color: #f4f4f4; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h2 style="margin: 0 0 10px 0; color: #2c3e50;">📖 {livro['titulo']}</h2>
            <h4 style="margin: 0 0 15px 0; color: #7f8c8d;">✍️ Autor: {livro['autor']}</h4>
            <p style="margin: 0;"><b>💡 O que você precisa saber hoje:</b> {livro['resumo']}</p>
        </div>
        <p>Foque nos estudos! Te amo!</p>
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
    livro = get_book_of_the_week()
    print(f"Livro selecionado para a semana: {livro['titulo']} - {livro['autor']}")
    
    if os.environ.get("TEST_RUN"):
        print("\nModo de teste: o e-mail não foi enviado.")
    else:
        print("\nIniciando envio do e-mail semanal...")
        send_email(livro)

if __name__ == "__main__":
    main()
