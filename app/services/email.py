import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import  SMTP_SENDER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

def send_email(recipient: str, subject: str, email_body: str, content_type):
    sender = SMTP_SENDER
    password = SMTP_PASSWORD
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT

    msg = MIMEMultipart("alternative")
    msg["FROM"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(email_body, content_type,'utf-8'))

    try:
        with smtplib.SMTP(smtp_server,smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"Письмо успешно улетело на адрес: {recipient}")

    except Exception as exc:
        print(f"Ошибка при отправке письма: {exc}")

    




