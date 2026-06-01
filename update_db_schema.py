import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_file = ".env.production" if os.getenv("ENV") == "production" else ".env.development"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def update_schema():
    print(f"Conectando ao banco de dados: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:
        # Se for PostgreSQL
        if engine.url.drivername.startswith("postgresql") or engine.url.drivername.startswith("postgres"):
            print("Executando migração de esquema no PostgreSQL...")
            
            # Adicionar coluna image_id
            conn.execute(text("""
                ALTER TABLE reports 
                ADD COLUMN IF NOT EXISTS image_id VARCHAR(36) 
                REFERENCES uploaded_files(id) 
                ON DELETE SET NULL;
            """))
            print("Coluna 'image_id' adicionada com sucesso ou já existente.")
            
            # Dropar coluna image_url antiga
            conn.execute(text("""
                ALTER TABLE reports 
                DROP COLUMN IF EXISTS image_url;
            """))
            print("Coluna 'image_url' antiga removida com sucesso.")
            
        else: # SQLite ou outro
            print("Executando migração de esquema no SQLite...")
            try:
                conn.execute(text("ALTER TABLE reports ADD COLUMN image_id VARCHAR(36) REFERENCES uploaded_files(id) ON DELETE SET NULL;"))
                print("Coluna 'image_id' adicionada.")
            except Exception as e:
                print(f"Aviso ao adicionar coluna image_id (pode ser que já exista): {e}")

            try:
                conn.execute(text("ALTER TABLE reports DROP COLUMN image_url;"))
                print("Coluna 'image_url' removida.")
            except Exception as e:
                print(f"Aviso ao remover coluna 'image_url': {e}")

    print("Esquema do banco de dados atualizado com sucesso!")

if __name__ == "__main__":
    update_schema()
