import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_file = ".env.production" if os.getenv("ENV") == "production" else ".env.development"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()  # fallback para .env padrao

DATABASE_URL = os.getenv("DATABASE_URL")

# Se for SQLite, precisa de parametros adicionais de thread
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
