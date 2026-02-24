"""
Auth Routes — реєстрація та вхід через PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.auth_service import (
    register_user,
    login_user,
    decode_token,
    generate_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ═══════════════════════════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ═══════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Реєстрація нового користувача з bcrypt хешуванням."""
    return register_user(
        db=db,
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        password=data.password,
    )


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Аутентифікація користувача через БД."""
    return login_user(db=db, username=data.username, password=data.password)
