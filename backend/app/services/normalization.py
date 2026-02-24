"""
NormalizationEngine — Min-Max нормалізація для Multi-Criteria Scoring.

Академічна модель (Weighted Sum Model / WSM):
  - Обчислює глобальні min/max для 5 критеріїв:
      1. Speed     (RPM)              — maximize
      2. Force     (Torque, Н·см)     — maximize
      3. Economy   (Ціна, грн)        — minimize
      4. Endurance (Маса, г)          — minimize
      5. Eco       (Energy, Вт)       — minimize

  - Нормалізація Min-Max:
      maximize: normalized = (x - min) / (max - min)
      minimize: normalized = 1 - (x - min) / (max - min)

  - Кешує межі при ініціалізації (один раз на сесію).
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, TypedDict


class Bounds(TypedDict):
    """Min/max для одного атрибута."""
    min: float
    max: float


# 5 критеріїв для нормалізації
CRITERIA = ("speed", "force", "economy", "endurance", "eco")

# Напрямок оптимізації: True = maximize, False = minimize
CRITERIA_DIRECTION: Dict[str, bool] = {
    "speed": True,       # maximize RPM
    "force": True,       # maximize Torque
    "economy": False,    # minimize Price
    "endurance": False,  # minimize Weight
    "eco": False,        # minimize Energy Consumption
}


class NormalizationEngine:
    """
    Кешуючий движок нормалізації.

    При ініціалізації обчислює глобальні та per-category межі
    для всіх 5 критеріїв. Потім використовується для нормалізації
    окремих значень компонентів.

    Usage:
        engine = NormalizationEngine(all_components)
        norm_speed = engine.normalize("speed", rpm_value, category="motor")
        norm_eco   = engine.normalize("eco", energy_value, category="motor")
    """

    def __init__(self, components: List[Dict[str, Any]]):
        self._components = components
        self._global_bounds: Dict[str, Bounds] = {}
        self._category_bounds: Dict[str, Dict[str, Bounds]] = {}
        self._compute_all_bounds()

    # ══════════════════════════════════════════════════════════════
    #  EXTRACTORS — як отримувати значення кожного критерію
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_speed(comp: Dict[str, Any]) -> Optional[float]:
        """RPM (оберти за хвилину) — із electronics.rpm_nominal."""
        elec = comp.get("electronics") or {}
        rpm = elec.get("rpm_nominal")
        return float(rpm) if rpm is not None else None

    @staticmethod
    def _extract_force(comp: Dict[str, Any]) -> Optional[float]:
        """Torque (Н·см) — із electronics.torque_nominal_ncm."""
        elec = comp.get("electronics") or {}
        torque = elec.get("torque_nominal_ncm")
        return float(torque) if torque is not None else None

    @staticmethod
    def _extract_economy(comp: Dict[str, Any]) -> Optional[float]:
        """Ціна (грн)."""
        price = comp.get("price")
        return float(price) if price is not None else None

    @staticmethod
    def _extract_endurance(comp: Dict[str, Any]) -> Optional[float]:
        """Маса (г)."""
        weight = comp.get("weight")
        return float(weight) if weight is not None else None

    @staticmethod
    def _extract_eco(comp: Dict[str, Any]) -> Optional[float]:
        """Energy Consumption (Вт) = voltage_v × max_current_a.

        Для компонентів без electronics → None (не впливає на еко-оцінку).
        """
        elec = comp.get("electronics") or {}
        voltage = elec.get("voltage_v")
        current = elec.get("max_current_a")
        if voltage is not None and current is not None:
            return float(voltage) * float(current)
        return None

    # Мапа критерій → extractor
    EXTRACTORS = {
        "speed": _extract_speed.__func__,
        "force": _extract_force.__func__,
        "economy": _extract_economy.__func__,
        "endurance": _extract_endurance.__func__,
        "eco": _extract_eco.__func__,
    }

    # ══════════════════════════════════════════════════════════════
    #  BOUNDS COMPUTATION
    # ══════════════════════════════════════════════════════════════

    def _compute_all_bounds(self) -> None:
        """Обчислює глобальні та per-category межі для всіх критеріїв."""

        # Групуємо по категоріях
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for comp in self._components:
            cat = comp.get("category", "unknown")
            by_cat.setdefault(cat, []).append(comp)

        # Глобальні межі
        self._global_bounds = self._compute_bounds_for_list(self._components)

        # Per-category межі
        for cat, comps in by_cat.items():
            self._category_bounds[cat] = self._compute_bounds_for_list(comps)

    def _compute_bounds_for_list(
        self, comps: List[Dict[str, Any]]
    ) -> Dict[str, Bounds]:
        """Обчислює межі для списку компонентів."""
        bounds: Dict[str, Bounds] = {}

        for criterion, extractor in self.EXTRACTORS.items():
            values: List[float] = []
            for comp in comps:
                val = extractor(comp)
                if val is not None:
                    values.append(val)
            if values:
                bounds[criterion] = {
                    "min": min(values),
                    "max": max(values),
                }

        return bounds

    # ══════════════════════════════════════════════════════════════
    #  NORMALIZATION
    # ══════════════════════════════════════════════════════════════

    def normalize(
        self,
        criterion: str,
        value: float,
        category: Optional[str] = None,
        use_global: bool = False,
    ) -> float:
        """
        Нормалізує значення за критерієм.

        Args:
            criterion:  Один з CRITERIA ("speed", "force", "economy", "endurance", "eco").
            value:      Сире значення для нормалізації.
            category:   Категорія компонента (для per-category меж).
            use_global: Якщо True — завжди використовувати глобальні межі.

        Returns:
            Нормалізоване значення в діапазоні [0.0, 1.0].
        """
        # Вибираємо bounds: per-category або global
        if not use_global and category and category in self._category_bounds:
            bounds_map = self._category_bounds[category]
        else:
            bounds_map = self._global_bounds

        if criterion not in bounds_map:
            return 0.0

        b = bounds_map[criterion]
        min_val = b["min"]
        max_val = b["max"]

        if max_val == min_val:
            return 1.0  # Всі значення однакові → максимальна оцінка

        is_maximize = CRITERIA_DIRECTION.get(criterion, True)

        if is_maximize:
            return (value - min_val) / (max_val - min_val)
        else:
            return 1.0 - (value - min_val) / (max_val - min_val)

    def normalize_component(
        self,
        comp: Dict[str, Any],
        use_global: bool = False,
    ) -> Dict[str, float]:
        """
        Нормалізує всі 5 критеріїв для одного компонента.

        Returns:
            Dict {"speed": 0.XX, "force": 0.XX, "economy": 0.XX,
                  "endurance": 0.XX, "eco": 0.XX}
        """
        category = comp.get("category", "unknown")
        result: Dict[str, float] = {}

        for criterion, extractor in self.EXTRACTORS.items():
            val = extractor(comp)
            if val is not None:
                result[criterion] = self.normalize(
                    criterion, val,
                    category=category, use_global=use_global,
                )
            else:
                result[criterion] = 0.0

        return result

    # ══════════════════════════════════════════════════════════════
    #  UTILITY
    # ══════════════════════════════════════════════════════════════

    def get_global_bounds(self) -> Dict[str, Bounds]:
        """Повертає глобальні межі (для логування/debug)."""
        return dict(self._global_bounds)

    def get_category_bounds(self, category: str) -> Dict[str, Bounds]:
        """Повертає межі для конкретної категорії."""
        return dict(self._category_bounds.get(category, {}))

    def extract_raw_value(
        self, criterion: str, comp: Dict[str, Any]
    ) -> Optional[float]:
        """Витягує сирое значення критерію з компонента."""
        extractor = self.EXTRACTORS.get(criterion)
        if extractor:
            return extractor(comp)
        return None
