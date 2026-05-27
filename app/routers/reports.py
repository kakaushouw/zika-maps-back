import os
import shutil
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date
from app.database import get_db
from app.models import Report, User
from app.schemas import ReportCreate, ReportResponse, ReportUpdateStatus
from app.auth import get_current_user, get_current_agent
from app.websocket import manager

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

def serialize_report(report: Report) -> dict:
    return {
        "id": report.id,
        "user_id": report.user_id,
        "description": report.description,
        "address": report.address,
        "status": report.status,
        "date": report.date.isoformat() if isinstance(report.date, date) else str(report.date),
        "lat": float(report.lat),
        "lng": float(report.lng),
        "image_url": report.image_url,
        "created_at": report.created_at.isoformat()
    }

@router.get("", response_model=List[ReportResponse])
def get_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return reports

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def add_report(report_in: ReportCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_report = Report(
        user_id=current_user.id,
        description=report_in.description or "Foco registrado via app",
        address=report_in.address,
        lat=Decimal(str(report_in.lat)),
        lng=Decimal(str(report_in.lng)),
        image_url=report_in.image_url,
        status="pending"
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Serializar e notificar via WebSocket
    report_data = serialize_report(db_report)
    await manager.broadcast_json({
        "eventType": "INSERT",
        "new": report_data
    })

    return db_report

@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(report_id: str, status_in: ReportUpdateStatus, current_agent: User = Depends(get_current_agent), db: Session = Depends(get_db)):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Denúncia não encontrada."
        )

    # Validar novo status
    valid_statuses = ["pending", "confirmed", "resolved", "discarded"]
    if status_in.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status inválido. Escolha um dos seguintes: {', '.join(valid_statuses)}"
        )

    db_report.status = status_in.status
    db.commit()
    db.refresh(db_report)

    # Serializar e notificar via WebSocket
    report_data = serialize_report(db_report)
    await manager.broadcast_json({
        "eventType": "UPDATE",
        "new": report_data
    })

    return db_report

@router.post("/upload")
def upload_file(request: Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Criar diretorio de uploads se nao existir
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Validar extensao
    allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
    ext = file.filename.split(".")[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Apenas imagens são aceitas ({', '.join(allowed_extensions)})."
        )

    # Nome seguro para o arquivo
    filename = f"{current_user.id}_{int(time.time())}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o arquivo."
        )

    # Construir URL estática pública
    # Ex: http://localhost:5000/static/uploads/filename.jpg
    base_url = str(request.base_url)
    public_url = f"{base_url}static/uploads/{filename}"

    return {"url": public_url}
