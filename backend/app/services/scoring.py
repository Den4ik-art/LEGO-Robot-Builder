"""
Модуль для обчислення зважених оцінок компонентів (WSM).

Реалізує 5-критерійну формулу Weighted Sum Model:
  speed, force, economy, endurance, eco.
Підтримує пресети пріоритетів та Eco-Mode.
"""

from typing import Dict, List, Any, Optional, TypedDict
from app.services.normalization import NormalizationEngine


class NormalizationBounds(TypedDict):
    """Межі min/max для нормалізації атрибута."""
    min: float
    max: float


class CategoryBounds(TypedDict, total=False):
    """Межі нормалізації для категорії компонентів."""
    price: NormalizationBounds
    weight: NormalizationBounds
    rpm: NormalizationBounds
    torque: NormalizationBounds
    energy: NormalizationBounds


class WeightedScorer:
    """
    Клас для обчислення зважених оцінок компонентів (WSM).

    5 критеріїв:
        - speed     → maximize rpm_nominal (electronics.rpm_nominal)
        - force     → maximize torque_nominal_ncm (electronics.torque_nominal_ncm)
        - economy   → minimize price
        - endurance → minimize weight (mass)
        - eco       → minimize energy_consumption (voltage × current)
    """

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "speed": 0.5,
        "force": 0.5,
        "economy": 0.5,
        "endurance": 0.5,
        "eco": 0.25,
    }

    # Ваги при активному Eco-Mode
    ECO_MODE_ADJUSTMENTS: Dict[str, float] = {
        "speed": -0.1,     # знижуємо пріоритет швидкості
        "force": 0.0,
        "economy": 0.0,
        "endurance": 0.0,
        "eco": +0.3,       # підвищуємо пріоритет енергоефективності
    }

    # Мапа пріоритетів на набори ваг (backward compatibility)
    PRIORITY_PRESETS: Dict[str, Dict[str, float]] = {
        "speed": {
            "speed": 1.0, "force": 0.5, "economy": 0.25,
            "endurance": 0.25, "eco": 0.1,
        },
        "stability": {
            "speed": 0.25, "force": 1.0, "economy": 0.25,
            "endurance": 0.5, "eco": 0.2,
        },
        "cheapness": {
            "speed": 0.25, "force": 0.25, "economy": 1.0,
            "endurance": 0.5, "eco": 0.3,
        },
        "durability": {
            "speed": 0.25, "force": 0.5, "economy": 0.5,
            "endurance": 1.0, "eco": 0.2,
        },
        "balanced": {
            "speed": 0.5, "force": 0.5, "economy": 0.5,
            "endurance": 0.5, "eco": 0.25,
        },
        "eco": {
            "speed": 0.3, "force": 0.4, "economy": 0.5,
            "endurance": 0.5, "eco": 0.8,
        },
    }

    def __init__(self, components: List[Dict[str, Any]]):
        """
        Ініціалізація скорера.

        Args:
            components: Список всіх компонентів для обчислення меж нормалізації.
        """
        self.components = components
        self._engine = NormalizationEngine(components)

        # Зберігаємо legacy bounds cache для backward compatibility
        self._bounds_cache: Dict[str, CategoryBounds] = {}
        self._compute_legacy_bounds()

    def _compute_legacy_bounds(self) -> None:
        """Legacy: обчислює межі в старому форматі (для backward compatibility)."""
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for comp in self.components:
            cat = comp.get("category", "unknown")
            by_category.setdefault(cat, []).append(comp)

        for category, comps in by_category.items():
            self._bounds_cache[category] = self._compute_category_bounds(comps)

    def _compute_category_bounds(self, comps: List[Dict[str, Any]]) -> CategoryBounds:
        """Обчислює межі для однієї категорії (legacy format)."""
        prices: List[float] = []
        weights: List[float] = []
        rpms: List[float] = []
        torques: List[float] = []
        energies: List[float] = []

        for c in comps:
            price = c.get("price")
            if price is not None:
                prices.append(float(price))

            weight = c.get("weight")
            if weight is not None:
                weights.append(float(weight))

            elec = c.get("electronics") or {}
            rpm = elec.get("rpm_nominal")
            if rpm is not None:
                rpms.append(float(rpm))

            torque = elec.get("torque_nominal_ncm")
            if torque is not None:
                torques.append(float(torque))

            # Energy = voltage * current
            voltage = elec.get("voltage_v")
            current = elec.get("max_current_a")
            if voltage is not None and current is not None:
                energies.append(float(voltage) * float(current))

        bounds: CategoryBounds = {}

        if prices:
            bounds["price"] = {"min": min(prices), "max": max(prices)}
        if weights:
            bounds["weight"] = {"min": min(weights), "max": max(weights)}
        if rpms:
            bounds["rpm"] = {"min": min(rpms), "max": max(rpms)}
        if torques:
            bounds["torque"] = {"min": min(torques), "max": max(torques)}
        if energies:
            bounds["energy"] = {"min": min(energies), "max": max(energies)}

        return bounds

    def get_bounds_for_category(self, category: str) -> CategoryBounds:
        """Повертає закешовані межі для категорії."""
        return self._bounds_cache.get(category, {})

    @staticmethod
    def _normalize_maximize(value: float, min_val: float, max_val: float) -> float:
        """Norm for maximization: (val - min) / (max - min)."""
        if max_val == min_val:
            return 1.0
        return (value - min_val) / (max_val - min_val)

    @staticmethod
    def _normalize_minimize(value: float, min_val: float, max_val: float) -> float:
        """Norm for minimization: 1 - (val - min) / (max - min)."""
        if max_val == min_val:
            return 1.0
        return 1.0 - (value - min_val) / (max_val - min_val)

    def calculate_component_score(
        self,
        component: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Обчислює зважену оцінку компонента (5-Term WSM).

        Formula:
            TotalScore = (norm_speed    × w_speed)
                       + (norm_torque   × w_force)
                       + (norm_price    × w_economy)
                       + (norm_mass     × w_endurance)
                       + (norm_energy   × w_eco)

        Args:
            component: Компонент для оцінки.
            weights:   Словник ваг {speed, force, economy, endurance, eco}.
                       Якщо None — використовуються дефолтні ваги.

        Returns:
            Загальна зважена оцінка (float).
        """
        if weights is None:
            weights = self.DEFAULT_WEIGHTS.copy()

        category = component.get("category", "unknown")
        bounds = self.get_bounds_for_category(category)

        # 5 ваг
        w_speed = weights.get("speed", 0.25)
        w_force = weights.get("force", 0.25)
        w_economy = weights.get("economy", 0.25)
        w_endurance = weights.get("endurance", 0.25)
        w_eco = weights.get("eco", 0.25)

        # --- Speed (rpm) - maximize ---
        normalized_speed = 0.0
        elec = component.get("electronics") or {}
        rpm = elec.get("rpm_nominal")
        if rpm is not None and "rpm" in bounds:
            rpm_bounds = bounds["rpm"]
            normalized_speed = self._normalize_maximize(
                float(rpm), rpm_bounds["min"], rpm_bounds["max"]
            )

        # --- Force (torque) - maximize ---
        normalized_torque = 0.0
        torque = elec.get("torque_nominal_ncm")
        if torque is not None and "torque" in bounds:
            torque_bounds = bounds["torque"]
            normalized_torque = self._normalize_maximize(
                float(torque), torque_bounds["min"], torque_bounds["max"]
            )

        # --- Economy (price) - minimize ---
        normalized_price_inv = 0.0
        price = component.get("price")
        if price is not None and "price" in bounds:
            price_bounds = bounds["price"]
            normalized_price_inv = self._normalize_minimize(
                float(price), price_bounds["min"], price_bounds["max"]
            )

        # --- Endurance (weight/mass) - minimize ---
        normalized_mass_inv = 0.0
        weight = component.get("weight")
        if weight is not None and "weight" in bounds:
            weight_bounds = bounds["weight"]
            normalized_mass_inv = self._normalize_minimize(
                float(weight), weight_bounds["min"], weight_bounds["max"]
            )

        # --- Eco (energy consumption) - minimize ---
        normalized_energy_inv = 0.0
        voltage = elec.get("voltage_v")
        current = elec.get("max_current_a")
        if voltage is not None and current is not None and "energy" in bounds:
            energy = float(voltage) * float(current)
            energy_bounds = bounds["energy"]
            normalized_energy_inv = self._normalize_minimize(
                energy, energy_bounds["min"], energy_bounds["max"]
            )

        # 5-Term WSM Formula
        total_score = (
            (normalized_speed * w_speed)
            + (normalized_torque * w_force)
            + (normalized_price_inv * w_economy)
            + (normalized_mass_inv * w_endurance)
            + (normalized_energy_inv * w_eco)
        )

        # ── Structural Value Bonus ──
        # Structural parts have 0 speed/force, so they lose to functional parts.
        # Compensate using their intrinsic structural scores (already in data).
        if category == "structure":
            scores_data = component.get("scores") or {}
            str_strength = scores_data.get("structural_strength", 0.0)
            str_versatility = scores_data.get("connection_versatility", 0.0)
            str_compactness = scores_data.get("compactness", 0.5)

            # Surface area contribution (normalized vs. max ~128 studs²)
            geo = component.get("geometry") or {}
            sl = geo.get("stud_length") or 0
            sw = geo.get("stud_width") or 0
            area = sl * sw
            area_norm = min(area / 128.0, 1.0) if area > 0 else 0.1

            # Blended structural value (replaces the missing speed/force)
            structural_value = (
                str_strength * 0.35
                + str_versatility * 0.25
                + area_norm * 0.25
                + str_compactness * 0.15
            )
            # Scale to match typical functional part score range (0.3-0.8)
            total_score += structural_value * 0.6

        return total_score

    def get_weights_from_priority(
        self,
        priority: Optional[str],
        eco_mode: bool = False,
    ) -> Dict[str, float]:
        """
        Конвертує формат priority (string) у набір ваг.

        Args:
            priority: Рядок пріоритету.
            eco_mode: Якщо True — застосовує ECO_MODE_ADJUSTMENTS.

        Returns:
            Словник ваг (5 критеріїв).
        """
        if priority and priority.lower() in self.PRIORITY_PRESETS:
            weights = self.PRIORITY_PRESETS[priority.lower()].copy()
        else:
            weights = self.DEFAULT_WEIGHTS.copy()

        if eco_mode:
            weights = self.apply_eco_mode(weights)

        return weights

    @classmethod
    def apply_eco_mode(cls, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Застосовує ECO_MODE_ADJUSTMENTS до ваг.

        Eco-Mode підвищує значення eco-критерію та знижує speed.
        """
        adjusted = dict(weights)
        for criterion, delta in cls.ECO_MODE_ADJUSTMENTS.items():
            current = adjusted.get(criterion, 0.25)
            adjusted[criterion] = max(0.1, min(1.0, current + delta))
        return adjusted

    def get_normalization_engine(self) -> NormalizationEngine:
        """Повертає NormalizationEngine для зовнішнього використання."""
        return self._engine
