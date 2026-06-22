"""
Централізовані обмеження та профілі складності для конфігуратора LEGO-робота.

Містить:
  - ComplexityProfile:  кількість моторів, сенсорів, структурних деталей
                        та якісний рівень для кожного рівня складності (1-5).
  - Terrain / Environment constraints.
  - "Golden Rules" — базові логічні обмеження для будь-якого робота.
"""

from __future__ import annotations
import random

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple


# ═════════════════════════════════════════════════════════════════════
#  COMPLEXITY PROFILES  (рівні 1-5)
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ComplexityProfile:
    """Профіль складності робота.

    Визначає кількісні обмеження для рівня complexity.
    """
    level: int

    # Мотори
    min_motors: int
    max_motors: int
    prefer_large_motors: bool  # True → L-Motor, False → M-Motor

    # Сенсори
    min_sensors: int
    max_sensors: int

    # Структура
    min_structure: int
    max_structure: int
    structure_reinforcement: float  # множник для кількості балок/пінів

    # Загальна різноманітність
    allow_gearbox: bool
    allow_manipulator: bool

    # Підсилення різноманітності популяції ГА
    ga_population_multiplier: float  # 1.0 = default, >1.0 = more diverse


COMPLEXITY_PROFILES: Dict[int, ComplexityProfile] = {
    1: ComplexityProfile(
        level=1,
        min_motors=1, max_motors=2,
        prefer_large_motors=False,
        min_sensors=0, max_sensors=0,
        min_structure=4, max_structure=8,
        structure_reinforcement=0.5,
        allow_gearbox=False,
        allow_manipulator=False,
        ga_population_multiplier=0.8,
    ),
    2: ComplexityProfile(
        level=2,
        min_motors=1, max_motors=2,
        prefer_large_motors=False,
        min_sensors=0, max_sensors=1,
        min_structure=6, max_structure=12,
        structure_reinforcement=0.8,
        allow_gearbox=False,
        allow_manipulator=True,
        ga_population_multiplier=1.0,
    ),
    3: ComplexityProfile(
        level=3,
        min_motors=2, max_motors=3,
        prefer_large_motors=False,
        min_sensors=1, max_sensors=2,
        min_structure=8, max_structure=16,
        structure_reinforcement=1.0,
        allow_gearbox=True,
        allow_manipulator=True,
        ga_population_multiplier=1.0,
    ),
    4: ComplexityProfile(
        level=4,
        min_motors=2, max_motors=4,
        prefer_large_motors=True,
        min_sensors=2, max_sensors=3,
        min_structure=10, max_structure=20,
        structure_reinforcement=1.3,
        allow_gearbox=True,
        allow_manipulator=True,
        ga_population_multiplier=1.3,
    ),
    5: ComplexityProfile(
        level=5,
        min_motors=3, max_motors=6,
        prefer_large_motors=True,
        min_sensors=3, max_sensors=5,
        min_structure=14, max_structure=25,
        structure_reinforcement=1.6,
        allow_gearbox=True,
        allow_manipulator=True,
        ga_population_multiplier=1.5,
    ),
}


def get_complexity_profile(level: int) -> ComplexityProfile:
    """Повертає профіль складності за рівнем (1-5, clamp).

    Рівень менше 1 → 1, більше 5 → 5.
    """
    clamped = max(1, min(5, level))
    return COMPLEXITY_PROFILES[clamped]


# ═════════════════════════════════════════════════════════════════════
#  ОБМЕЖЕННЯ МІСЦЕВОСТІ / СЕРЕДОВИЩА
# ═════════════════════════════════════════════════════════════════════

TERRAIN_ALLOWED_DOMAINS: Dict[str, List[str]] = {
    "indoor":        ["ground", "universal"],
    "outdoor_flat":  ["ground", "universal"],
    "offroad":       ["ground", "universal"],
    "water_pool":    ["water", "universal"],
    "air":           ["air", "universal"],
}


def get_terrain_domains(terrain: str) -> List[str]:
    """Повертає допустимі домени для типу поверхні."""
    return TERRAIN_ALLOWED_DOMAINS.get(
        terrain.lower(), ["ground", "universal"]
    )


# ═════════════════════════════════════════════════════════════════════
#  "GOLDEN RULES" — базові логічні обмеження
# ═════════════════════════════════════════════════════════════════════

# Категорії, що кваліфікуються як "структурна база" (Base-First Rule)
BASE_CATEGORIES: Set[str] = {"structure"}
BASE_FAMILIES: Set[str] = {
    "plate", "brick", "panel", "hull_frame", "technic_beam",
}
BASE_MIN_SIZE: str = "medium"  # Мінімальний size_class для бази


def is_valid_base(comp: Dict[str, Any]) -> bool:
    """Перевіряє, чи компонент може слугувати структурною базою робота.

    Правила:
      - category == 'structure'
      - family ∈ BASE_FAMILIES
      - geometry.size_class ∈ {'medium', 'large'}  (не 'small')
    """
    if comp.get("category") != "structure":
        return False
    family = comp.get("family", "")
    if family not in BASE_FAMILIES:
        return False
    size_class = (comp.get("geometry") or {}).get("size_class", "medium")
    if size_class == "small":
        return False
    return True


# Допустимі кількості коліс (Symmetry Rule)
ALLOWED_WHEEL_COUNTS = {2, 4, 6}


def get_symmetric_wheel_count(requested: int) -> int:
    """Округлює до найближчого допустимого числа коліс.

    Наприклад: 1→2, 3→4, 5→6, 7→6.
    """
    if requested <= 0:
        return 2
    best = min(ALLOWED_WHEEL_COUNTS, key=lambda x: abs(x - requested))
    return best


# Максимальна кількість портів за типом хабу
DEFAULT_HUB_PORTS = 4
MAX_HUB_PORTS = 6


def get_max_motor_power(hub: Dict[str, Any]) -> float:
    """Повертає максимальну потужність що хаб може забезпечити (мВт).

    Якщо невідомо — повертає велике значення (без обмежень).
    """
    electronics = hub.get("electronics") or {}
    return electronics.get("max_power_mw", float("inf"))


def check_power_balance(
    hub: Dict[str, Any],
    motors: List[Dict[str, Any]],
) -> bool:
    """Перевіряє, чи хаб може живити всі мотори.

    Повертає True якщо загальна необхідна потужність ≤ max_power хабу.
    Якщо хаб не має даних про потужність — завжди True.
    """
    max_power = get_max_motor_power(hub)
    if max_power == float("inf"):
        return True
    total_motor_power = sum(
        (m.get("electronics") or {}).get("power_mw", 0) for m in motors
    )
    return total_motor_power <= max_power


def check_port_count(
    hub: Dict[str, Any],
    motor_count: int,
    sensor_count: int,
) -> bool:
    """Перевіряє, чи достатньо портів хабу для моторів + сенсорів."""
    max_ports = (hub.get("electronics") or {}).get("ports_count", DEFAULT_HUB_PORTS)
    return (motor_count + sensor_count) <= max_ports


# ═════════════════════════════════════════════════════════════════════
#  ПРІОРИТЕТ ЯКОСТІ МОТОРІВ (якість > кількість)
# ═════════════════════════════════════════════════════════════════════

def prefer_large_motor(comp: Dict[str, Any]) -> bool:
    """Перевіряє чи мотор є "великим" (L-Motor / XL-Motor).

    Евристика: назва містить L або великий крутний момент.
    """
    name = (comp.get("name") or "").lower()
    if "angular" in name or "l-motor" in name or "xl" in name:
        return True
    torque = (comp.get("electronics") or {}).get("torque_nominal_ncm", 0)
    if torque and torque > 20:
        return True
    return False


# ═════════════════════════════════════════════════════════════════════
#  СТРУКТУРНА ЦІЛІСНІСТЬ — масштаб та шасі
# ═════════════════════════════════════════════════════════════════════

# Мінімальна площа в stud² для «фундаменту» робота
_MIN_BASE_AREA = 20  # ~4×6 plate

# Скільки stud² «потрібно» кожному функціональному компоненту
_AREA_PER_MOTOR = 12      # один L-Motor займає ~3×4 stud²
_AREA_PER_HUB = 20        # хаб EV3/Spike ~5×4
_AREA_PER_SENSOR = 6      # сенсор ~2×3

# Множники складності: 1 → 0.8, 2 → 1.0, 3 → 1.2, 4 → 1.4, 5 → 1.6
_COMPLEXITY_SCALE = {1: 0.8, 2: 1.0, 3: 1.2, 4: 1.4, 5: 1.6}


def compute_stud_area(comp: Dict[str, Any]) -> int:
    """Обчислює площу деталі в stud² (stud_length × stud_width).

    Якщо geometry відсутня — повертає оцінку за size_class:
      small → 2, medium → 8, large → 24.
    """
    geo = comp.get("geometry") or {}
    sl = geo.get("stud_length") or 0
    sw = geo.get("stud_width") or 0
    area = sl * sw
    if area > 0:
        return area
    # Fallback за size_class
    sc = geo.get("size_class", "small")
    return {"small": 2, "medium": 8, "large": 24}.get(sc, 4)


def compute_connection_points(comp: Dict[str, Any]) -> int:
    """Сумарна кількість точок з'єднання деталі (studs, holes, pins)."""
    total = 0
    for c in comp.get("connectors") or []:
        total += c.get("count", 0)
    return total


def compute_structural_requirement(
    motor_count: int,
    hub_count: int = 1,
    sensor_count: int = 0,
    complexity: int = 2,
) -> Dict[str, Any]:
    """Розраховує мінімальні структурні вимоги для робота.

    Returns:
        dict з ключами:
          min_stud_area:         мінімальна площа бази (stud²)
          min_connection_points: мін. к-ть точок з'єднання
          recommended_families:  рекомендовані типи деталей
    """
    mult = _COMPLEXITY_SCALE.get(complexity, 1.0)
    base_area = (
        motor_count * _AREA_PER_MOTOR
        + hub_count * _AREA_PER_HUB
        + sensor_count * _AREA_PER_SENSOR
    )
    min_area = max(_MIN_BASE_AREA, int(base_area * mult))
    min_conns = motor_count * 2 + hub_count * 4

    recommended = ["frame", "plate"]
    if complexity >= 3 or motor_count >= 3:
        recommended.insert(0, "technic_beam")

    return {
        "min_stud_area": min_area,
        "min_connection_points": min_conns,
        "recommended_families": recommended,
    }


def check_structural_adequacy(
    structure_parts: List[Dict[str, Any]],
    motor_count: int,
    hub_count: int = 1,
    sensor_count: int = 0,
    complexity: int = 2,
) -> Tuple[bool, float]:
    """Перевіряє, чи достатньо структурних деталей для підтримки функціональних.

    Returns:
        (is_adequate, coverage_ratio) — ratio ≥ 1.0 = достатньо.
    """
    req = compute_structural_requirement(
        motor_count, hub_count, sensor_count, complexity,
    )
    total_area = sum(compute_stud_area(p) for p in structure_parts)
    ratio = total_area / max(1, req["min_stud_area"])
    return ratio >= 1.0, min(ratio, 3.0)


def find_adequate_base(
    components: List[Dict[str, Any]],
    motor_count: int,
    complexity: int = 2,
    max_price: float = float("inf"),
    max_weight: float = float("inf"),
    allowed_domains: Optional[set] = None,
) -> Optional[Dict[str, Any]]:
    """Знаходить найкращу структурну базу що задовольняє масштабні вимоги.

    Пріоритет: frame/plate з достатньою площею за найнижчу ціну.
    """
    req = compute_structural_requirement(motor_count, 1, 0, complexity)
    min_area = req["min_stud_area"]

    candidates = []
    for c in components:
        if c.get("category") != "structure":
            continue
        if not is_valid_base(c):
            continue
        price = c.get("price") or 0
        weight = c.get("weight") or 0
        if price > max_price or weight > max_weight:
            continue
        area = compute_stud_area(c)
        # Кандидат повинен мати хоча б 60% від потрібної площі
        if area < min_area * 0.6:
            continue
        candidates.append((c, area, price))

    if not candidates:
        return None

    # Сортуємо: деталі що покривають мін. площу
    adequate = [x for x in candidates if x[1] >= min_area]
    if adequate:
        # Для різноманітності ( Diversity Rule):
        # 40% ймовірність обрати brick/frame замість найдешевшої plate,
        # або якщо складність висока (>=3).
        prefer_bricks = random.random() < 0.4 or complexity >= 3
        if prefer_bricks:
            bricks = [x for x in adequate if x[0].get("family") in ("brick", "frame", "panel")]
            if bricks:
                bricks.sort(key=lambda x: x[2]) # найдешевший з блоків
                return bricks[0][0]

        # Стандарт: найдешевший адекватний компонент (зазвичай plate)
        adequate.sort(key=lambda x: x[2])
        return adequate[0][0]

    # Якщо немає ідеальних — беремо найбільшу за площею
    candidates.sort(key=lambda x: -x[1])
    return candidates[0][0]


# ═════════════════════════════════════════════════════════════════════
#  ОБМЕЖЕННЯ ОБ'ЄМНОГО СПІВВІДНОШЕННЯ
#  Обсяг структури >= Σ(обсяг функц. компонентів) × 1.5
# ═════════════════════════════════════════════════════════════════════

_VOLUME_CLASS_MAP = {"Small": 2, "Medium": 8, "Large": 24}


def get_component_volume(comp: Dict[str, Any]) -> int:
    """Обчислює об'єм компонента в stud² (stud_length × stud_width).

    Fallback через volume_class або geometry.size_class.
    """
    geo = comp.get("geometry") or {}
    sl = geo.get("stud_length") or 0
    sw = geo.get("stud_width") or 0
    if sl > 0 and sw > 0:
        return sl * sw
    vc = comp.get("volume_class") or geo.get("size_class", "Small")
    return _VOLUME_CLASS_MAP.get(vc, _VOLUME_CLASS_MAP.get(vc.capitalize() if isinstance(vc, str) else "Small", 4))


def check_volume_ratio(
    structural_parts: List[Dict[str, Any]],
    functional_parts: List[Dict[str, Any]],
    ratio: float = 1.5,
) -> Tuple[bool, float]:
    """Перевіряє Volume Ratio constraint.

    Structural_Volume >= Sum(Functional_Volume) * ratio.

    Returns:
        (is_satisfied, actual_ratio)
    """
    struct_vol = sum(get_component_volume(p) for p in structural_parts) or 1
    func_vol = sum(get_component_volume(p) for p in functional_parts) or 1
    actual_ratio = struct_vol / func_vol
    return actual_ratio >= ratio, round(actual_ratio, 2)


# ═════════════════════════════════════════════════════════════════════
#  ПРАВИЛО МАСШТАБУ — обов'язкова велика структурна деталь
# ═════════════════════════════════════════════════════════════════════

def needs_large_structural(
    complexity: int,
    motor_count: int,
) -> bool:
    """Перевіряє чи потрібна хоча б одна Large структурна деталь.

    Правило: Complexity > 2 OR Motor Count > 2 → потрібна Large деталь.
    """
    return complexity > 2 or motor_count > 2


def has_large_structural(parts: List[Dict[str, Any]]) -> bool:
    """Перевіряє чи є хоча б одна Large структурна деталь серед частин."""
    for p in parts:
        if p.get("category") != "structure":
            continue
        vc = p.get("volume_class") or (p.get("geometry") or {}).get("size_class", "small")
        if isinstance(vc, str) and vc.lower() == "large":
            return True
    return False


def find_large_structural(
    components: List[Dict[str, Any]],
    max_price: float = float("inf"),
    max_weight: float = float("inf"),
) -> Optional[Dict[str, Any]]:
    """Знаходить найкращу Large структурну деталь (за площею / ціною)."""
    candidates = []
    for c in components:
        if c.get("category") != "structure":
            continue
        vc = c.get("volume_class") or (c.get("geometry") or {}).get("size_class", "small")
        if isinstance(vc, str) and vc.lower() != "large":
            continue
        price = c.get("price") or 0
        weight = c.get("weight") or 0
        if price > max_price or weight > max_weight:
            continue
        area = compute_stud_area(c)
        candidates.append((c, area, price))

    if not candidates:
        return None

    # Пріоритет: найбільша площа за розумну ціну
    candidates.sort(key=lambda x: (-x[1], x[2]))
    return candidates[0][0]


# ═════════════════════════════════════════════════════════════════════
#  CONNECTOR FILL — Заповнення недостатніх з'єднань
# ═════════════════════════════════════════════════════════════════════

# Мінімальні вимоги до з'єднувальних деталей per motor
_CONNECTOR_REQUIREMENTS = {
    "axle": 1,       # мін. 1 вісь на мотор
    "technic_pin": 2, # мін. 2 піна на мотор
}


def compute_connector_deficit(
    chosen_parts: List[Dict[str, Any]],
    motor_count: int,
) -> Dict[str, int]:
    """Обчислює скільки з'єднувальних деталей не вистачає.

    Returns:
        dict {family: deficit_count} — скільки ще потрібно додати.
    """
    # Підрахунок існуючих з'єднувальних деталей
    existing: Dict[str, int] = {}
    for p in chosen_parts:
        fam = p.get("family", "")
        if fam in ("axle", "technic_pin", "technic_connector", "gear"):
            existing[fam] = existing.get(fam, 0) + 1

    # Обчислюємо дефіцит
    deficit: Dict[str, int] = {}
    for family, per_motor in _CONNECTOR_REQUIREMENTS.items():
        needed = motor_count * per_motor
        have = existing.get(family, 0)
        if have < needed:
            deficit[family] = needed - have

    return deficit


def find_connector_parts(
    components: List[Dict[str, Any]],
    family: str,
    count: int,
    max_price: float = float("inf"),
    max_weight: float = float("inf"),
) -> List[Dict[str, Any]]:
    """Знаходить з'єднувальні деталі потрібного типу.

    Returns:
        Список до count найдешевших деталей.
    """
    candidates = [
        c for c in components
        if c.get("category") == "structure"
        and c.get("family") == family
        and (c.get("price") or 0) <= max_price
        and (c.get("weight") or 0) <= max_weight
    ]
    if not candidates:
        return []

    # Сортуємо за ціною (найдешевші)
    candidates.sort(key=lambda c: c.get("price") or 0)
    best = candidates[0]
    return [best] * min(count, 10)  # Repeat best connector


# ═════════════════════════════════════════════════════════════════════
#  СТРУКТУРНІ ВИМОГИ ДО ФУНКЦІЙ
# ═════════════════════════════════════════════════════════════════════

# Політ → потрібна легка, але велика рама
# Їзда → потрібна міцна базова плита
# Плавання → потрібен корпус/водонепроникна рама

FUNCTION_STRUCTURAL_HINTS: Dict[str, Dict[str, Any]] = {
    "літати": {
        "preferred_families": ["plate", "technic_beam"],
        "prefer_lightweight": True,
        "min_size": "medium",
        "volume_ratio": 1.2,   # літаючі роботи — менше вимог до маси
    },
    "їздити": {
        "preferred_families": ["frame", "plate", "brick"],
        "prefer_lightweight": False,
        "min_size": "medium",
        "volume_ratio": 1.5,
    },
    "плавати": {
        "preferred_families": ["hull_frame", "plate"],
        "prefer_lightweight": True,
        "min_size": "medium",
        "volume_ratio": 1.3,
    },
    "маніпулювати": {
        "preferred_families": ["technic_beam", "frame"],
        "prefer_lightweight": False,
        "min_size": "small",
        "volume_ratio": 1.0,
    },
}


def get_function_structural_hint(functions: List[str]) -> Dict[str, Any]:
    """Повертає агреговані структурні вимоги для набору функцій.

    Обирає найвимогливіший volume_ratio і об'єднує preferred families.
    """
    result = {
        "preferred_families": set(),
        "prefer_lightweight": False,
        "min_size": "small",
        "volume_ratio": 1.5,
    }

    for func in functions:
        func_l = func.lower()
        for key, hint in FUNCTION_STRUCTURAL_HINTS.items():
            if key in func_l:
                result["preferred_families"].update(hint["preferred_families"])
                if hint["prefer_lightweight"]:
                    result["prefer_lightweight"] = True
                # Найвимогливіший ratio
                result["volume_ratio"] = max(
                    result["volume_ratio"], hint["volume_ratio"]
                )
                # Найбільший min_size
                size_order = {"small": 0, "medium": 1, "large": 2}
                if size_order.get(hint["min_size"], 0) > size_order.get(
                    result["min_size"], 0
                ):
                    result["min_size"] = hint["min_size"]

    result["preferred_families"] = list(
        result["preferred_families"]
    ) or ["plate", "frame"]

    return result


# ═════════════════════════════════════════════════════════════════════
#  ФАЗА ДЕКОРУ — естетичне заповнення за бюджетом
# ═════════════════════════════════════════════════════════════════════

# Категорії деталей для декоративного заповнення
DECOR_FAMILIES = [
    "plate", "brick", "tile", "panel",
    "technic_pin", "technic_connector",
]

DECOR_ENGINEERING_ROLES = {"Decorative", "Connection"}


def select_decor_parts(
    components: List[Dict[str, Any]],
    remaining_budget: float,
    remaining_mass: float,
    target_budget_usage: float = 0.95,
    original_budget: float = 0.0,
) -> List[Dict[str, Any]]:
    """Підбирає декоративні / з'єднувальні деталі для заповнення бюджету.

    Правило: якщо remaining_budget > 10% від оригінального бюджету,
    додаємо деталі з роллю Decorative або Connection до 95% використання.

    Returns:
        Список деталей для додавання.
    """
    if original_budget <= 0:
        return []

    budget_usage = 1.0 - (remaining_budget / original_budget)
    if budget_usage >= target_budget_usage:
        return []  # Бюджет вже використано достатньо

    # Збираємо кандидатів
    candidates = []
    for c in components:
        eng_role = c.get("engineering_role", "")
        fam = c.get("family", "")
        cat = c.get("category", "")

        # Деталі Decorative або Connection ролі
        is_decor = eng_role in DECOR_ENGINEERING_ROLES
        # Або маленькі структурні деталі (пластини, цеглинки)
        is_small_struct = (
            cat == "structure"
            and fam in DECOR_FAMILIES
            and (c.get("volume_class") or "Small") in ("Small", "Medium")
        )

        if not (is_decor or is_small_struct):
            continue

        price = c.get("price") or 0
        weight = c.get("weight") or 0
        if price <= 0 or price > remaining_budget or weight > remaining_mass:
            continue

        candidates.append(c)

    if not candidates:
        return []

    # Сортуємо: спочатку дешевші (щоб набрати більше різноманітності)
    candidates.sort(key=lambda c: c.get("price") or 0)

    result: List[Dict[str, Any]] = []
    budget_left = remaining_budget
    mass_left = remaining_mass
    target_remaining = original_budget * (1.0 - target_budget_usage)

    # Чергуємо різні типи для естетики
    used_families: Dict[str, int] = {}
    max_per_family = 4  # не більше 4 штук одного типу

    for c in candidates:
        if budget_left <= target_remaining:
            break

        fam = c.get("family", "unknown")
        if used_families.get(fam, 0) >= max_per_family:
            continue

        price = c.get("price") or 0
        weight = c.get("weight") or 0

        if price <= budget_left and weight <= mass_left:
            result.append(c)
            budget_left -= price
            mass_left -= weight
            used_families[fam] = used_families.get(fam, 0) + 1

    return result
