from fastapi import APIRouter, HTTPException, Header
from app.db.repo import Repo
from app.models.dto import ConfigRequest
from app.services.greedy import GreedyConfigurator
from app.api.auth.routes_auth import decode_token
from pathlib import Path
from datetime import datetime
import json

router = APIRouter(prefix="/config", tags=["Configurator"])

@router.post("")
def generate_configuration(request: ConfigRequest, authorization: str = Header(None)):
    repo = Repo()
    components = repo.get_all_components()

    if not components:
        raise HTTPException(status_code=404, detail="База компонентів порожня")

    configurator = GreedyConfigurator(components)
    result = configurator.configure(request)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # --- Логування історії користувача ---
    history_file = Path(__file__).resolve().parent.parent / "db" / "history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
    except json.JSONDecodeError:
        history = []

    user_id = "anonymous"
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            user_id = decode_token(token)
        except Exception:
            user_id = "anonymous"

    entry = {
        "user_id": user_id,
        "request": request.dict(),
        "result": result,
        "timestamp": str(datetime.utcnow())
    }

    history.append(entry)
    history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

    return result
