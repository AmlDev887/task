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
from typing import Annotated
from datetime 
celery = Celery("task", broker="redis://localhost:6379/0")
redis_client =  redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True)


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
    
