"""
Repository — доступ до компонентів через PostgreSQL.

Замінює JSON-based Repo на DB-based.
Зберігає зворотню сумісність: get_all_components() повертає List[Dict].
"""

import logging
from typing import List, Dict
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_session_factory
from app.models.models import Component

logger = logging.getLogger(__name__)


class Repo:
    """
    Repository для LEGO-компонентів.

    Зворотньо сумісний — повертає List[Dict], як раніше з JSON.
    Оптимізатори (Greedy, Genetic) працюють з цим без змін.
    """

    def __init__(self, db: Session = None):
        self._db = db
        self._owns_session = False

    def _get_db(self) -> Session:
        if self._db:
            return self._db
        self._db = get_session_factory()()
        self._owns_session = True
        return self._db

    def get_all_components(self) -> List[Dict]:
        """
        Повертає всі компоненти як List[Dict].
        Завантажує конектори для повноти даних.
        """
        db = self._get_db()
        try:
            components = (
                db.query(Component)
                .options(joinedload(Component.connectors))
                .all()
            )

            if not components:
                logger.warning("[WARN] Компоненти не знайдено в БД. Перехід на JSON fallback.")
                return self._fallback_json()

            return [comp.to_dict() for comp in components]
        except Exception as e:
            logger.error(f"Помилка отримання компонентів: {e}")
            # Fallback до JSON якщо БД недоступна
            return self._fallback_json()
        finally:
            if self._owns_session and self._db:
                self._db.close()
                self._db = None

    def get_component_by_id(self, component_id: int) -> Dict:
        """Отримує один компонент за ID."""
        db = self._get_db()
        try:
            comp = (
                db.query(Component)
                .options(joinedload(Component.connectors))
                .filter(Component.id == component_id)
                .first()
            )
            return comp.to_dict() if comp else {}
        finally:
            if self._owns_session and self._db:
                self._db.close()
                self._db = None

    def get_components_by_category(self, category: str) -> List[Dict]:
        """Отримує компоненти за категорією."""
        db = self._get_db()
        try:
            components = (
                db.query(Component)
                .options(joinedload(Component.connectors))
                .filter(Component.category == category)
                .all()
            )
            return [comp.to_dict() for comp in components]
        finally:
            if self._owns_session and self._db:
                self._db.close()
                self._db = None

    def _fallback_json(self) -> List[Dict]:
        """Fallback — читає з JSON якщо БД недоступна."""
        import json
        from pathlib import Path

        data_path = Path(__file__).parent.parent / "data" / "lego_components.json"
        if not data_path.exists():
            logger.error(f"[WARN] JSON-файл {data_path} також не знайдено")
            return []
        with open(data_path, "r", encoding="utf-8") as f:
            logger.info("Fallback: завантаження з JSON-файлу")
            return json.load(f)
