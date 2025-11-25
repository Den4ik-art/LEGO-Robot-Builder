from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import jwt, datetime, json
from uuid import uuid4
from pathlib import Path
from typing import Optional

SECRET_KEY = "supersecretkey"

router = APIRouter(prefix="/auth", tags=["Auth"])

# === Файл користувачів ===
data_path = Path(__file__).resolve().parent.parent.parent / "data" / "users.json"
data_path.parent.mkdir(exist_ok=True)
if not data_path.exists():
    data_path.write_text("[]", encoding="utf-8")

# === Моделі ===
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

# === Утиліти ===
def load_users():
    return json.loads(data_path.read_text(encoding="utf-8"))

def save_users(users):
    data_path.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")

def generate_token(user_id: str):
    payload = {
        "id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> Optional[str]:
    """
    Перевіряє JWT токен і повертає ID користувача, якщо токен валідний.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен протерміновано")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недійсний токен")

# === Ендпоінти ===
@router.post("/register")
def register(data: RegisterRequest):
    users = load_users()

    if any(u["username"] == data.username for u in users):
        raise HTTPException(status_code=400, detail="Користувач із таким логіном вже існує")

    new_user = {
        "id": str(uuid4()),
        "username": data.username,
        "email": data.email,
        "full_name": data.full_name,
        "password": data.password
    }

    users.append(new_user)
    save_users(users)

    token = generate_token(new_user["id"])

    return {
        "message": "Реєстрація успішна",
        "user": {"username": new_user["username"], "full_name": new_user["full_name"]},
        "token": token
    }

@router.post("/login")
def login(data: LoginRequest):
    users = load_users()
    user = next((u for u in users if u["username"] == data.username and u["password"] == data.password), None)

    if not user:
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")

    token = generate_token(user["id"])

    return {
        "message": "Вхід успішний",
        "user": {"username": user["username"], "full_name": user["full_name"]},
        "token": token
    }
