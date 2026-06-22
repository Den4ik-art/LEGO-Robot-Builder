from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db, get_session_factory
from app.db.repo import Repo
from app.models.dto import ConfigRequest
from app.models.models import Configuration, ConfigurationPart
from app.services.sequential import SequentialConfigurator
from app.services.genetic import GeneticAlgorithmOptimizer
from app.services.auth_service import decode_token
from datetime import datetime
import json
import threading
import queue

router = APIRouter(prefix="/config", tags=["Configurator"])


def _save_configuration_to_db(
    db: Session,
    user_id: str,
    request: ConfigRequest,
    result: dict,
    algorithm: str = "greedy",
) -> int:
    """Зберігає результат конфігурації в БД та повертає ID."""
    try:
        config = Configuration(
            user_id=user_id if user_id != "anonymous" else None,
            name=f"Config {algorithm.capitalize()}",
            request_data=request.dict(),
            total_price=float(result.get("total_price", 0)),
            total_weight=float(result.get("total_weight", 0)),
            remaining_budget=float(result.get("remaining_budget", 0)),
            result_data=result,
            algorithm=algorithm,
        )
        db.add(config)
        db.flush()

        # Зберігаємо обрані компоненти
        selected = result.get("selected", [])
        seen_ids = {}
        for part in selected:
            part_id = part.get("id")
            if part_id:
                if part_id in seen_ids:
                    seen_ids[part_id] += 1
                else:
                    seen_ids[part_id] = 1

        for comp_id, qty in seen_ids.items():
            config_part = ConfigurationPart(
                configuration_id=config.id,
                component_id=comp_id,
                quantity=qty,
            )
            db.add(config_part)

        db.commit()
        return config.id
    except Exception as e:
        db.rollback()
        # Не зупиняємо відповідь через помилку логування
        import logging
        logging.getLogger(__name__).error(f"Помилка збереження конфігурації: {e}")
        return 0


@router.post("")
def generate_configuration(
    request: ConfigRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    repo = Repo(db=db)
    components = repo.get_all_components()

    if not components:
        raise HTTPException(status_code=404, detail="База компонентів порожня")

    configurator = SequentialConfigurator(components)
    result = configurator.configure(request)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # --- Логування історії в БД ---
    user_id = "anonymous"
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            user_id = decode_token(token)
        except Exception:
            user_id = "anonymous"

    config_id = _save_configuration_to_db(db, user_id, request, result, algorithm="greedy")
    result["id"] = config_id

    return result


@router.post("/genetic")
def genetic_optimization(
    request: ConfigRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Генетичний алгоритм оптимізації конфігурації робота.

    Повертає Server-Sent Events (SSE) потік:
      - progress events: {"progress": int, "total": int, "status": str}
      - result event:    {"result": {...final config...}}
    """
    repo = Repo(db=db)
    components = repo.get_all_components()

    if not components:
        raise HTTPException(status_code=404, detail="База компонентів порожня")

    # Визначення user_id
    user_id = "anonymous"
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            user_id = decode_token(token)
        except Exception:
            user_id = "anonymous"

    # Черга для передачі прогресу з потоку GA в SSE генератор
    progress_queue: queue.Queue = queue.Queue()
    result_holder: dict = {}
    error_holder: dict = {}

    def progress_callback(current: int, total: int, status: str):
        """Callback що викликається GA кожні N поколінь."""
        progress_queue.put({
            "type": "progress",
            "progress": current,
            "total": total,
            "status": status,
        })

    def run_ga():
        """Запускає GA в окремому потоці."""
        try:
            optimizer = GeneticAlgorithmOptimizer(
                components,
                population_size=80,
                generations=150,
                mutation_rate=0.08,
                crossover_rate=0.75,
                tournament_size=5,
                elitism_pct=0.05,
            )
            result = optimizer.optimize(request, progress_callback=progress_callback)
            result_holder["data"] = result

            # Зберігаємо в БД
            save_db = get_session_factory()()
            try:
                config_id = _save_configuration_to_db(save_db, user_id, request, result, algorithm="genetic")
                result["id"] = config_id
            finally:
                save_db.close()

        except Exception as e:
            error_holder["error"] = str(e)
        finally:
            progress_queue.put({"type": "done"})

    # get_session_factory імпортовано на рівні модуля

    # Запускаємо GA в окремому потоці
    ga_thread = threading.Thread(target=run_ga, daemon=True)
    ga_thread.start()

    def event_stream():
        """Генератор SSE подій."""
        while True:
            try:
                msg = progress_queue.get(timeout=30)
            except queue.Empty:
                # Timeout — надсилаємо heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                continue

            if msg["type"] == "done":
                # GA завершився
                if "error" in error_holder:
                    yield f"data: {json.dumps({'type': 'error', 'error': error_holder['error']})}\n\n"
                elif "data" in result_holder:
                    yield f"data: {json.dumps({'type': 'result', 'result': result_holder['data']}, ensure_ascii=False, default=str)}\n\n"
                break
            else:
                # оновлення прогресу
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
