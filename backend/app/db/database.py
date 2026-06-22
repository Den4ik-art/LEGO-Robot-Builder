"""
Database connection and session management.

Підтримує PostgreSQL (production) та SQLite (development/fallback).
Конфігурація через змінні оточення (.env).

Lazy initialization — engine створюється тільки при першому використанні,
що дозволяє додатку стартувати навіть якщо БД недоступна.
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  URL БД
# ═══════════════════════════════════════════════════════════════════

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    ""
)

# ═══════════════════════════════════════════════════════════════════
#  ЛІНИВО-ІНІЦІАЛІЗОВАНИЙ РУШІЙ ТА СЕСІЯ
# ═══════════════════════════════════════════════════════════════════

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None
_db_available: bool = False


def _resolve_database_url() -> str:
    """Визначає URL бази даних з конфігурації або fallback на SQLite."""
    url = DATABASE_URL.strip()

    if url and url.startswith("postgresql"):
        # Перевіряємо чи доступний psycopg2
        try:
            import psycopg2  # noqa: F401
            logger.info(f"Використовується PostgreSQL: {url.split('@')[-1] if '@' in url else url}")
            return url
        except ImportError:
            logger.warning(
                "psycopg2 не доступний на цій системі. "
                "Використовується SQLite як fallback для розробки."
            )

    # Резервний варіант: SQLite
    from pathlib import Path
    db_dir = Path(__file__).resolve().parent.parent / "data"
    db_dir.mkdir(exist_ok=True)
    sqlite_path = db_dir / "lego_configurator.db"
    sqlite_url = f"sqlite:///{sqlite_path}"
    logger.info(f"Використовується SQLite: {sqlite_path}")
    return sqlite_url


def get_engine() -> Engine:
    """Lazy engine creation — створює engine при першому виклику."""
    global _engine
    if _engine is None:
        db_url = _resolve_database_url()
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            _engine = create_engine(
                db_url,
                connect_args=connect_args,
                echo=False,
            )
        else:
            _engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,
            )
    return _engine


def get_session_factory() -> sessionmaker:
    """Lazy session factory creation."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


# Зворотня сумісність — можна імпортувати SessionLocal напряму
class _LazySessionLocal:
    """Proxy що дозволяє використовувати SessionLocal() без попереднього виклику."""
    def __call__(self):
        return get_session_factory()()

SessionLocal = _LazySessionLocal()


def get_db():
    """
    FastAPI Dependency — повертає сесію БД.
    Використання:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Створює всі таблиці, визначені в Base.metadata.
    Викликається при старті додатку.
    """
    try:
        from app.db.base import Base
        # Імпортуємо моделі щоб вони зареєструвались в Base.metadata
        import app.models.models  # noqa: F401

        engine = get_engine()
        Base.metadata.create_all(bind=engine)

        global _db_available
        _db_available = True
        logger.info("[OK] Всі таблиці створено успішно")
    except Exception as e:
        logger.error(f"[ERROR] Помилка створення таблиць: {e}")
        raise


def is_db_available() -> bool:
    """Перевіряє чи база даних доступна."""
    return _db_available
