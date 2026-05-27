import os
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_file = ".env.production" if os.getenv("ENV") == "production" else ".env.development"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

from app.database import engine, Base
from app.models import User, Profile, UserRole, Report

def init_db():
    print(f"Carregando banco de dados usando: {os.getenv('DATABASE_URL')}")
    print("Criando tabelas no banco de dados...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    init_db()
