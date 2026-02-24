"""
SQLAlchemy Base class — єдина точка імпорту для всіх моделей.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовий клас для всіх SQLAlchemy моделей."""
    pass
