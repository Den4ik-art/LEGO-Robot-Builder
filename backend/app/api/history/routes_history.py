"""
History Routes — отримання та очищення історії конфігурацій через PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import decode_token
from app.models.auto_generated_models import Configuration

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
