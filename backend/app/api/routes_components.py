"""
Components Routes — отримання компонентів із PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repo import Repo

router = APIRouter(prefix="/components", tags=["Components"])


@router.get("")
def get_components(db: Session = Depends(get_db)):
    """Повертає список усіх доступних LEGO-компонентів."""
    repo = Repo(db=db)
    components = repo.get_all_components()

    if not components:
        raise HTTPException(status_code=404, detail="Компоненти не знайдено")

    return components
