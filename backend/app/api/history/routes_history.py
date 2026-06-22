"""
History Routes — отримання та очищення історії конфігурацій через PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import decode_token
from app.models.models import Configuration
from app.services.pdf_generator import generate_robot_passport
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/list")
def get_history(
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    """Повертає історію конфігурацій для поточного користувача."""
    if not token:
        raise HTTPException(status_code=401, detail="Токен відсутній")

    try:
        user_id = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Недійсний токен")

    configs = (
        db.query(Configuration)
        .filter(Configuration.user_id == user_id)
        .order_by(Configuration.created_at.desc())
        .all()
    )

    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "request": c.request_data,
            "result": c.result_data,
            "total_price": c.total_price,
            "total_weight": c.total_weight,
            "remaining_budget": c.remaining_budget,
            "algorithm": c.algorithm,
            "timestamp": str(c.created_at) if c.created_at else None,
        }
        for c in configs
    ]


@router.delete("/clear")
def clear_history(
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    """Видаляє історію конфігурацій для поточного користувача."""
    if not token:
        raise HTTPException(status_code=401, detail="Токен відсутній")

    try:
        user_id = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Недійсний токен")

    deleted = (
        db.query(Configuration)
        .filter(Configuration.user_id == user_id)
        .delete()
    )
    db.commit()

    return {"message": "Історію успішно очищено", "deleted_count": deleted}

@router.post("/{config_id}/export/pdf")
def export_pdf(
    config_id: int,
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    """Експортує конфігурацію у PDF-формат (через ID із БД)."""
    if not token:
        raise HTTPException(status_code=401, detail="Токен відсутній")

    try:
        user_id = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Недійсний токен")

    config = db.query(Configuration).filter(Configuration.id == config_id, Configuration.user_id == user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Конфігурацію не знайдено")

    config_data = {
        "id": config.id,
        "request": config.request_data,
        "result": config.result_data,
        "total_price": config.total_price,
        "total_weight": config.total_weight,
        "remaining_budget": config.remaining_budget,
        "algorithm": config.algorithm,
        "timestamp": str(config.created_at) if config.created_at else None,
    }

    try:
        pdf_bytes = generate_robot_passport(config_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка генерації PDF: {str(e)}")

    response = StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename=robot_passport_{config_id}.pdf"
    return response


@router.post("/export/pdf/direct")
def export_pdf_direct(
    data: dict,
):
    """Експортує конфігурацію у PDF напряму з даних (без авторизації)."""
    try:
        pdf_bytes = generate_robot_passport(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Помилка генерації PDF: {str(e)}")

    config_id = data.get("id", 0)
    response = StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename=robot_passport_{config_id}.pdf"
    return response
