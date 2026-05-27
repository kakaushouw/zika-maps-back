import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_file = ".env.production" if os.getenv("ENV") == "production" else ".env.development"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

# Importar banco de dados para inicializacao automatica das tabelas
from app.database import engine, Base
# Importar modelos para registrar no Base
from app.models import User, Profile, UserRole, Report

# Inicializar tabelas do banco de dados (se nao existirem)
try:
    Base.metadata.create_all(bind=engine)
    print("Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar o banco de dados: {e}")

# Criar app FastAPI
app = FastAPI(
    title="ZikaMaps API",
    description="API BackEnd em Python/FastAPI para monitoramento do Aedes aegypti",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Configurar CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
origins = [
    frontend_url,
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar pasta de uploads se nao existir
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir arquivos de imagem estáticos
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="static")

# Registrar Routers
from app.routers import auth, reports
app.include_router(auth.router)
app.include_router(reports.router)

# WebSocket Realtime Endpoint
from app.websocket import manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Manter a conexao ativa e escutar mensagens do cliente
            data = await websocket.receive_text()
            # Pode responder ping se necessario
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "ZikaMaps BackEnd API está rodando com sucesso!",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development")
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
