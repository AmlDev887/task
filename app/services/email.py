import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import  SMTP_SENDER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT

def send_email(recipient: str, subject: str, body: str):
    sender = SMTP_SENDER
    password = SMTP_PASSWORD
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT

    msg = MIMEMultipart()
    msg["FROM"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body,"plain"))

    with smtplib.SMTP(smtp_server,smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        


