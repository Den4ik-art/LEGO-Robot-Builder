"""
Auth Service — автентифікація з bcrypt + JWT через PostgreSQL.

Замінює JSON-based авторизацію на повноцінну DB-based.
"""

import os
import datetime
import logging
from typing import Optional

import bcrypt
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.auto_generated_models import User
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey-change-in-production")
ALGORITHM: str = "HS256"
TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "1"))


# ═══════════════════════════════════════════════════════════════════
#  PASSWORD HASHING
# ═══════════════════════════════════════════════════════════════════

def hash_password(plain_password: str) -> str:
    """Хешує пароль за допомогою bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє пароль проти bcrypt хешу."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════
#  JWT TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def generate_token(user_id: str) -> str:
    """Генерує JWT токен для користувача."""
    payload = {
        "id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRE_DAYS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """
    Перевіряє JWT токен і повертає user_id.
    Кидає HTTPException при невалідному/протермінованому токені.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Недійсний токен: відсутній id")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен протерміновано")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недійсний токен")


# ═══════════════════════════════════════════════════════════════════
#  USER OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def register_user(
    db: Session,
    username: str,
    email: str,
    full_name: str,
    password: str,
) -> dict:
    """
    Реєстрація нового користувача.
    Повертає dict з user info та JWT token.
    """
    # Перевірка на дублікат username
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Користувач із таким логіном вже існує")

    # Перевірка на дублікат email
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Користувач із такою електронною поштою вже існує")

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = generate_token(user.id)

    logger.info(f"Зареєстровано нового користувача: {username}")

    return {
        "message": "Реєстрація успішна",
        "user": {"username": user.username, "full_name": user.full_name},
        "token": token,
    }


def login_user(db: Session, username: str, password: str) -> dict:
    """
    Аутентифікація користувача.
    Повертає dict з user info та JWT token.
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")

    token = generate_token(user.id)

    logger.info(f"Успішний вхід: {username}")

    return {
        "message": "Вхід успішний",
        "user": {"username": user.username, "full_name": user.full_name},
        "token": token,
    }


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Отримує користувача за ID."""
    return db.query(User).filter(User.id == user_id).first()
