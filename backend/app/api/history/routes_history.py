from fastapi import APIRouter, HTTPException, Header
from app.api.auth.routes_auth import decode_token
from pathlib import Path
import json

router = APIRouter(prefix="/history", tags=["History"])

HISTORY_FILE = Path(__file__).resolve().parent.parent.parent / "db" / "history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Завантаження історії ---
def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

# --- Збереження історії ---
def save_history(data):
    HISTORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# === Отримання історії ===
@router.get("/list")
def get_history(token: str = Header(None)):
    """
    Повертає історію лише для поточного користувача.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Токен відсутній")

    try:
        user_id = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Недійсний токен")

    history = load_history()
    user_history = [h for h in history if h.get("user_id") == user_id]
    return user_history


# === Очищення історії ===
@router.delete("/clear")
def clear_history(token: str = Header(None)):
    """
    Видаляє історію лише для поточного користувача.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Токен відсутній")

    try:
        user_id = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Недійсний токен")

    history = load_history()
    # Залишаємо лише записи інших користувачів
    updated_history = [h for h in history if h.get("user_id") != user_id]

    save_history(updated_history)

    return {"message": "Історію успішно очищено ✅"}
