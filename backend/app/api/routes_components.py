from fastapi import APIRouter, HTTPException
from app.db.repo import Repo

router = APIRouter(prefix="/components", tags=["Components"])

@router.get("")
def get_components():
    """
    Повертає список усіх доступних LEGO-компонентів.
    """
    repo = Repo()
    components = repo.get_all_components()

    if not components:
        raise HTTPException(status_code=404, detail="Компоненти не знайдено")

    return components
