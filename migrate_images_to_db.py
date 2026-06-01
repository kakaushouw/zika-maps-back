import os
import mimetypes
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import inspect, text

# Carregar variaveis de ambiente
env_file = ".env.production" if os.getenv("ENV") == "production" else ".env.development"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

from app.database import engine, SessionLocal, Base
from app.models import UploadedFile

def migrate():
    # Garantir que todas as tabelas (incluindo uploaded_files) existam no banco
    print("Garantindo que todas as tabelas estejam criadas...")
    Base.metadata.create_all(bind=engine)

    # Verificar se a coluna antiga 'image_url' existe na tabela 'reports'
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('reports')]
    
    if 'image_url' not in columns:
        print("\nA coluna 'image_url' antiga não existe mais no banco de dados.")
        print("Tudo já foi normalizado! Não há arquivos antigos pendentes de migração.")
        return

    db = SessionLocal()
    try:
        # Buscar denúncias que possuem links antigos na coluna image_url
        query = text("SELECT id, image_url FROM reports WHERE image_url IS NOT NULL AND image_url LIKE '%/static/uploads/%'")
        reports_to_migrate = db.execute(query).fetchall()
        
        migrated_count = 0
        skipped_count = 0
        missing_files_count = 0

        upload_dir = os.getenv("UPLOAD_DIR", "uploads")

        print(f"Buscando denúncias com imagens locais para migrar (encontradas: {len(reports_to_migrate)})...")

        for row in reports_to_migrate:
            report_id, old_image_url = row.id, row.image_url
            
            # Extrair o nome do arquivo da URL
            parsed_url = urlparse(old_image_url)
            filename = os.path.basename(parsed_url.path)
            
            file_path = os.path.join(upload_dir, filename)

            if os.path.exists(file_path):
                print(f"Migrando imagem '{filename}' da denúncia {report_id}...")
                
                try:
                    # Ler o arquivo
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    # Identificar Content-Type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        ext = filename.split(".")[-1].lower()
                        mime_type = f"image/{ext}"

                    # Criar registro de UploadedFile
                    uploaded_file = UploadedFile(
                        filename=filename,
                        content_type=mime_type,
                        data=file_data
                    )
                    db.add(uploaded_file)
                    db.flush()  # Para obter o ID gerado

                    # Atualizar o image_id na denúncia
                    update_query = text("UPDATE reports SET image_id = :image_id WHERE id = :report_id")
                    db.execute(update_query, {"image_id": uploaded_file.id, "report_id": report_id})
                    
                    db.commit()
                    migrated_count += 1
                    print(f"Sucesso! Imagem vinculada via chave estrangeira.")
                except Exception as e:
                    db.rollback()
                    print(f"Erro ao migrar {filename}: {e}")
            else:
                missing_files_count += 1
                print(f"Aviso: Arquivo físico '{filename}' não encontrado em '{file_path}' para o report {report_id}")

        print("\n=== Resumo da Migração ===")
        print(f"Imagens migradas com sucesso: {migrated_count}")
        print(f"Arquivos físicos não encontrados: {missing_files_count}")

    finally:
        db.close()

if __name__ == "__main__":
    migrate()
