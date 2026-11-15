import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import  settings
from fastapi.templating import Jinja2Templates


def send_email(recipient: str, subject: str, email_body: str, content_type):
    sender = settings.SMTP_SENDER
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(email_body, content_type,'utf-8'))

    try:
        with smtplib.SMTP(smtp_server,smtp_port) as server:
            server.sendmail(sender, recipient, msg.as_string())
        print(f"Письмо успешно улетело на адрес: {recipient}")

    except Exception as exc:
        print(f"Ошибка при отправке письма: {exc}")

    




