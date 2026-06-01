import os
import urllib.parse
from sqlalchemy import create_engine, text
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

# Se for PostgreSQL, tentar criar o banco de dados se ele não existir
if DATABASE_URL and (DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")):
    try:
        parsed = urllib.parse.urlparse(DATABASE_URL)
        db_name = parsed.path.lstrip('/')
        
        # Conectar temporariamente ao banco padrao 'postgres' para rodar o CREATE DATABASE
        postgres_url = DATABASE_URL.replace(f"/{db_name}", "/postgres")
        
        # PostgreSQL exige isolamento AUTOCOMMIT para rodar CREATE DATABASE
        temp_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            # Checar se o banco ja existe
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name}
            )
            exists = result.scalar() is not None
            
            if not exists:
                print(f"Banco de dados '{db_name}' não encontrado no PostgreSQL. Criando...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Banco de dados '{db_name}' criado com sucesso!")
            else:
                print(f"Banco de dados PostgreSQL '{db_name}' já existe.")
        temp_engine.dispose()
    except Exception as e:
        print(f"Aviso ao tentar criar banco de dados PostgreSQL automaticamente: {e}")
        print("A aplicação tentará se conectar diretamente ao banco configurado.")

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
