from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

user = "postgres"
password = "amalbek2004"
host = "127.0.0.1"
port = 5432
database = "task"


engine = create_engine(f"postgres + psycopg2://{user}:{password}@{host}:{port}/{database}")

SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






