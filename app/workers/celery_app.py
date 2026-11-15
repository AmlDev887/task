from email.mime.text import MIMEText
from celery import Celery
import smtplib
import secrets
import redis
from fastapi import Depends, HTTPException, status
from app.core.config import settings
from app.models.models import EmailTokens
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services import email
from fastapi.templating import Jinja2Templates

celery = Celery("task", broker="redis://localhost:6379/0")
redis_client =  redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True)
templates = Jinja2Templates(directory=".")

@celery.task
def get_email_code(email: str,code):
   
    msg = MIMEText(f"Ваш код для входа: {code} ")
    msg["Subject"] = "Код для авторизации"
    msg["From"] = "proinvest@gmail.com"
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login("xolmurodov@gmail.com","surface")
        server.sendmail(msg["From"],[email], msg.as_string())
    
@celery.task
def get_email_user(email_author,email_user,text):
    
    msg = MIMEText(text)
    msg["Subject"] = "Вас упоменули"
    msg["From"] = email_author
    msg["To"] = email_user

    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login(email_author,"surface")
        server.sendmail(msg["From"],[email_user], msg.as_string())


@celery.task(bind=True, max_retries=5)
def get_email_task(self, 
                   recipient: str,
                   subject: str,
                   context_data: dict = None,
                   body: str = None, 
                   template_name : str= None):
    """Отправка сообщения в email"""
        
    try:
        if template_name is not None:
                template = templates.get_template(template_name)
                email_body = template.render(context_data or {})
                content_type = "html"
        else:
                email_body = body
                content_type = "plain"

        email.send_email(recipient, subject, email_body, content_type=content_type)
        
        return {"message": "Отправлено сообщение"}
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)