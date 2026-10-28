from email.mime.text import MIMEText
from celery import Celery
import smtplib
import secrets
import redis


celery = Celery("task", broker="redis://localhost:6379/0")
redis_client =  redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)

@celery.task
def get_email_code(email: str):
    code = secrets.randbelow(900000) + 100000
    msg = MIMEText(f"Ваш код для входа: {code} ")
    msg["Subject"] = "Код для авторизации"
    msg["From"] = "proinvest@gmail.com"
    msg["To"] = email
    
    redis_client.set(name=email, value=code, ex=300)
    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login("xolmurodov@gmail.com","surface")
        server.sendmail(msg["From"],[email], msg.as_string())
    
    print ("Отправлено!")
