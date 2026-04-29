import requests
import hashlib
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION (Uses Environment Variables for Cloud/Security) ---
TARGET_URL = os.environ.get("TARGET_URL", "https://www.state.gov/foreign-terrorist-organizations/")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # DO NOT hardcode password for GitHub
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
HASH_FILE = "last_hash.txt" # Relative path for GitHub repo
# ---------------------

def get_page_hash(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        return hashlib.sha256(content.encode('utf-8')).hexdigest(), content
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None, None

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def monitor():
    current_hash, content = get_page_hash(TARGET_URL)
    if not current_hash:
        return

    if not os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'w') as f:
            f.write(current_hash)
        print("Initial hash saved. Monitoring started.")
        return

    with open(HASH_FILE, 'r') as f:
        last_hash = f.read().strip()

    if current_hash != last_hash:
        print("Change detected!")
        send_email(
            subject=f"Webpage update: {TARGET_URL}",
            body=f"The monitored webpage has changed!\nOld hash: {last_hash}\nNew hash: {current_hash}\nURL: {TARGET_URL}"
        )
        with open(HASH_FILE, 'w') as f:
            f.write(current_hash)
    else:
        print("No change detected.")

if __name__ == "__main__":
    monitor()
