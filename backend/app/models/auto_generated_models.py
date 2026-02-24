"""
SQLAlchemy ORM-моделі бази даних.

Таблиці:
  - users              : Користувачі з bcrypt хешуванням паролів
  - categories          : Категорії компонентів (motor, sensor, wheel, ...)
  - components          : LEGO-компоненти з усіма полями
  - component_connectors: Конектори компонентів (окрема таблиця)
  - compatibility_rules : Правила сумісності (реляційна таблиця)
  - configurations      : Збережені конфігурації роботів
  - configuration_parts : Зв'язок конфігурація ↔ компоненти
"""

import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint, JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


# ═══════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════

class User(Base):
    """Модель користувача з bcrypt хешуванням."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    configurations: Mapped[List["Configuration"]] = relationship(
        "Configuration", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ═══════════════════════════════════════════════════════════════════
#  CATEGORIES
# ═══════════════════════════════════════════════════════════════════

class Category(Base):
    """Категорії компонентів (motor, sensor, wheel, controller, ...)."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    components: Mapped[List["Component"]] = relationship(
        "Component", back_populates="category_rel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


# ═══════════════════════════════════════════════════════════════════
#  COMPONENTS
# ═══════════════════════════════════════════════════════════════════

class Component(Base):
    """
    Повна модель LEGO-компонента.

    Скалярні поля зберігаються як колонки.
    Складні вкладені об'єкти (geometry, mechanical, electronics, scores, meta,
    constraints, inventory, question_weights) зберігаються як JSON.
    """
    __tablename__ = "components"

    # --- Primary ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Extended scalar fields ---
    lego_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="universal")
    system_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ABS")
    primary_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assembly_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    probability_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=1.0)

    # --- JSON fields (nested objects) ---
    geometry: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mechanical: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    electronics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    constraints: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    compatibility: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    inventory: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    question_weights: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    phys_props: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- Array fields as JSON ---
    roles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    domains: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    requires: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    excludes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # --- Relationships ---
    category_rel: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="components"
    )
    connectors: Mapped[List["ComponentConnector"]] = relationship(
        "ComponentConnector", back_populates="component", cascade="all, delete-orphan"
    )
    compatibility_rules_parent: Mapped[List["CompatibilityRule"]] = relationship(
        "CompatibilityRule",
        foreign_keys="CompatibilityRule.parent_component_id",
        back_populates="parent_component",
        cascade="all, delete-orphan",
    )
    compatibility_rules_child: Mapped[List["CompatibilityRule"]] = relationship(
        "CompatibilityRule",
        foreign_keys="CompatibilityRule.child_component_id",
        back_populates="child_component",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_components_category_family", "category", "family"),
        Index("ix_components_domain", "domain"),
    )

    def to_dict(self) -> dict:
        """Конвертує модель назад у dict (для сумісності з існуючими оптимізаторами)."""
        result = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "weight": self.weight,
            "image": self.image,
            "lego_number": self.lego_number,
            "family": self.family,
            "domain": self.domain,
            "system_type": self.system_type,
            "color": self.color,
            "material": self.material,
            "primary_role": self.primary_role,
            "is_base": self.is_base,
            "assembly_group": self.assembly_group,
            "probability_weight": self.probability_weight,
            "geometry": self.geometry,
            "mechanical": self.mechanical,
            "electronics": self.electronics,
            "constraints": self.constraints,
            "compatibility": self.compatibility,
            "scores": self.scores,
            "inventory": self.inventory,
            "meta": self.meta,
            "question_weights": self.question_weights,
            "phys_props": self.phys_props,
            "roles": self.roles,
            "domains": self.domains,
            "requires": self.requires,
            "excludes": self.excludes,
            "connectors": [c.to_dict() for c in self.connectors] if self.connectors else [],
        }
        return result

    def __repr__(self) -> str:
        return f"<Component(id={self.id}, name={self.name}, category={self.category})>"


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT CONNECTORS
# ═══════════════════════════════════════════════════════════════════

class ComponentConnector(Base):
    """Конектор компонента — окрема нормалізована таблиця."""
    __tablename__ = "component_connectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connector_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pattern: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    grid_step_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    orientation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    position: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    compatible_types: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    max_load_n: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_primary_connection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    component: Mapped["Component"] = relationship("Component", back_populates="connectors")

    def to_dict(self) -> dict:
        return {
            "id": self.connector_id,
            "type": self.type,
            "count": self.count,
            "pattern": self.pattern,
            "grid_step_mm": self.grid_step_mm,
            "orientation": self.orientation,
            "position": self.position,
            "compatible_types": self.compatible_types,
            "max_load_n": self.max_load_n,
            "is_primary_connection": self.is_primary_connection,
        }

    def __repr__(self) -> str:
        return f"<ComponentConnector(id={self.id}, type={self.type}, component_id={self.component_id})>"


# ═══════════════════════════════════════════════════════════════════
#  COMPATIBILITY RULES
# ═══════════════════════════════════════════════════════════════════

class CompatibilityRule(Base):
    """
    Правила сумісності між компонентами.

    Підтримує:
      - Component-to-Component (parent → child)
      - Category-based compatibility
      - Connection type / port matching
    """
    __tablename__ = "compatibility_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Component-level ---
    parent_component_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=True, index=True
    )
    child_component_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # --- Category-level ---
    parent_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    child_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # --- Connection matching ---
    connection_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    port_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # --- Rule metadata ---
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="compatible"
    )  # compatible | incompatible | requires
    system_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    parent_component: Mapped[Optional["Component"]] = relationship(
        "Component", foreign_keys=[parent_component_id], back_populates="compatibility_rules_parent"
    )
    child_component: Mapped[Optional["Component"]] = relationship(
        "Component", foreign_keys=[child_component_id], back_populates="compatibility_rules_child"
    )

    __table_args__ = (
        Index("ix_compat_parent_child", "parent_component_id", "child_component_id"),
        Index("ix_compat_categories", "parent_category", "child_category"),
        Index("ix_compat_connection", "connection_type", "port_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<CompatibilityRule(id={self.id}, "
            f"parent={self.parent_component_id or self.parent_category}, "
            f"child={self.child_component_id or self.child_category}, "
            f"type={self.rule_type})>"
        )


# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════

class Configuration(Base):
    """Збережена конфігурація робота."""
    __tablename__ = "configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Request parameters (JSON)
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Result summary
    total_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remaining_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Result data (full JSON of the result)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    algorithm: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # greedy | genetic

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="configurations")
    parts: Mapped[List["ConfigurationPart"]] = relationship(
        "ConfigurationPart", back_populates="configuration", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Configuration(id={self.id}, user_id={self.user_id})>"


# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION PARTS
# ═══════════════════════════════════════════════════════════════════

class ConfigurationPart(Base):
    """Зв'язок конфігурація ↔ компоненти (many-to-many з кількістю)."""
    __tablename__ = "configuration_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    configuration_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("configurations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    configuration: Mapped["Configuration"] = relationship("Configuration", back_populates="parts")
    component: Mapped["Component"] = relationship("Component")

    __table_args__ = (
        UniqueConstraint("configuration_id", "component_id", name="uq_config_component"),
    )

    def __repr__(self) -> str:
        return f"<ConfigurationPart(config={self.configuration_id}, component={self.component_id}, qty={self.quantity})>"
