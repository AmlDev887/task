from celery import Celery
from email.mime.text import MIMEText
from fastapi import Depends
import secrets
import smtplib

celery = Celery("task", broker="redis://localhost:6379/0")

def email_code():
    
    return (secrets.randblow(900000) + 100000)

@celery.task("/")
def get_email_code(email: str, code: int = Depends(email_code)):
    msg = MIMEText(f"Ваш код для входа: {code} ")
    msg["Subject"] = "Код для авторизации"
    msg["From"] = "proinvest@gmail.com"
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login("xolmurodovamalbek442@gmail.com","amalbek2004A")
        server.sendmail(msg["From"],[email], msg.as_string())
    
    return code
