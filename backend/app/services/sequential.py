"""
Sequential Configuration Constructor для LEGO-робота.

Реалізує покроковий алгоритм складання:
  Step 1: Hub (контролер)
  Step 2: Мотори (по портах хаба)
  Step 3: Периферія (колеса / гусениці / пропелери до кожного мотора)
  Step 4: Сенсори
  Step 5: Структурні елементи (каркас, осі, піни)
  Step 6: Живлення (батарея / блок)

Кожен крок перевіряє обмеження бюджету та маси.
Результат: стандартизований Configuration (список part IDs — "Seed" для ГА).
"""

from typing import List, Dict, Any, Optional, Tuple
from app.models.dto import ConfigRequest, PriorityWeights
from app.services.scoring import WeightedScorer
from app.services.constraints import (
    compute_structural_requirement,
    find_adequate_base,
    compute_stud_area,
)


# ── Константи: мапа функцій → тип периферії ──────────────────────────

FUNCTION_PERIPHERY_MAP: Dict[str, Dict[str, str]] = {
    "їздити": {
        "гусениці": "track",
        "колеса": "wheel",
        "крокуючий": "leg",
    },
    "літати": {
        "квадрокоптер": "propeller",
        "квадрокoptер": "propeller",
        "вертоліт": "propeller",
        "літак": "propeller",
    },
    "плавати": {
        "гребні гвинти": "water",
        "водомет": "water",
        "плавники": "water",
    },
    "маніпулювати": {
        "клішня (захват)": "manipulator",
        "лінійний актуатор": "manipulator",
        "вакуумна присоска": "manipulator",
        "біонічна рука": "manipulator",
    },
}

# Скільки моторів потрібно для кожної функції + периферії на мотор
FUNCTION_MOTOR_MAP: Dict[str, Dict[str, Tuple[int, int]]] = {
    # func -> {subtype: (motors, periphery_per_motor)}
    "їздити": {
        "колеса": (2, 2),     # 2 мотори, 2 колеса на мотор
        "гусениці": (2, 1),   # 2 мотори, 1 гусениця на мотор
        "крокуючий": (2, 1),
    },
    "літати": {
        "квадрокоптер": (4, 1),
        "вертоліт": (1, 1),
        "літак": (2, 1),
    },
    "плавати": {
        "гребні гвинти": (2, 1),
        "водомет": (2, 1),
        "плавники": (2, 1),
    },
    "маніпулювати": {
        "клішня (захват)": (1, 1),
        "лінійний актуатор": (1, 1),
        "вакуумна присоска": (1, 0),
        "біонічна рука": (1, 1),
    },
}

# Домени що дозволені для компонентів кожної функції
FUNCTION_DOMAINS: Dict[str, List[str]] = {
    "їздити": ["ground", "universal"],
    "літати": ["air", "universal"],
    "плавати": ["water", "universal"],
    "маніпулювати": ["universal"],
    "сканувати": ["universal"],
}


class SequentialConfigurator:
    """
    Покроковий конструктор LEGO-робота.

    Послідовність:
      1. Hub → 2. Motors (per port) → 3. Periphery → 4. Sensors
      → 5. Structure → 6. Power

    На кожному кроці перевіряється budget та max_mass.
    """

    # Псевдо-категорії → базова категорія
    ALIAS_CATEGORY: Dict[str, str] = {
        "wing": "structure",
        "wing_plate": "structure",
        "wheel_offroad": "wheel",
        "tire_offroad": "tire",
    }

    def __init__(self, components: List[Dict[str, Any]]):
        self.components = components
        self._normalize_components()
        self._index = self._build_category_index()
        self._scorer = WeightedScorer(components)

    # ──────────────────────────────────────────────────────────────────
    #  НОРМАЛІЗАЦІЯ ТА ІНДЕКСАЦІЯ
    # ──────────────────────────────────────────────────────────────────

    def _normalize_components(self) -> None:
        """Гарантує наявність дефолтних полів у кожному компоненті."""
        for comp in self.components:
            cat = comp.get("category", "")
            # domain
            domain = comp.get("domain")
            if not domain:
                if cat in ("water",):
                    comp["domain"] = "water"
                elif cat in ("propeller",):
                    comp["domain"] = "air"
                elif cat in ("wheel", "tire", "track", "tread"):
                    comp["domain"] = "ground"
                else:
                    comp["domain"] = "universal"
            # safety defaults
            comp.setdefault("geometry", {})
            comp.setdefault("scores", {})
            comp.setdefault("connectors", [])
            comp.setdefault("roles", [])
            comp.setdefault("electronics", {})
            comp.setdefault("family", None)
            # Infer family for structure
            if cat == "structure" and not comp.get("family"):
                comp["family"] = self._infer_family(comp)

    @staticmethod
    def _infer_family(comp: Dict) -> Optional[str]:
        """Евристика визначення сімейства структурного компонента."""
        name = (comp.get("name") or "").lower()
        if "кри" in name or "пластина-крило" in name or "клин (крило)" in name:
            return "wing_plate"
        if "пластина" in name or "plate" in name:
            return "plate"
        if "цегл" in name or "brick" in name:
            return "brick"
        if "панель" in name or "panel" in name:
            return "panel"
        if "техніч" in name or "technic" in name:
            if "балк" in name or "beam" in name:
                return "technic_beam"
            if "конектор" in name or "connector" in name:
                return "technic_connector"
            if "пін" in name or "pin" in name:
                return "technic_pin"
            if "ось" in name or "вісь" in name or "axle" in name:
                return "axle"
            if "шестерн" in name or "gear" in name:
                return "gear"
        if "шестерн" in name or "gear" in name:
            return "gear"
        if "корпус" in name or "hull" in name or "рама" in name:
            return "hull_frame"
        return None

    def _build_category_index(self) -> Dict[str, List[Dict]]:
        """Індекс компонентів за категоріями."""
        idx: Dict[str, List[Dict]] = {}
        for comp in self.components:
            cat = comp.get("category", "unknown")
            idx.setdefault(cat, []).append(comp)
        return idx

    # ──────────────────────────────────────────────────────────────────
    #  ДОПОМІЖНІ МЕТОДИ
    # ──────────────────────────────────────────────────────────────────

    def _resolve_weights(self, request: ConfigRequest) -> Dict[str, float]:
        """Отримує ваги з запиту (нові weights → або preset з priority)."""
        if request.weights is not None:
            return {
                "speed": request.weights.speed,
                "force": request.weights.force,
                "economy": request.weights.economy,
                "endurance": request.weights.endurance,
            }
        return self._scorer.get_weights_from_priority(request.priority)

    def _fits(
        self, comp: Dict, remaining_budget: float, remaining_mass: float
    ) -> bool:
        """Перевіряє чи компонент вміщується в бюджет та масу."""
        price = comp.get("price") or 0
        weight = comp.get("weight") or 0
        return price <= remaining_budget and weight <= remaining_mass

    def _select_best(
        self,
        category: str,
        weights: Dict[str, float],
        remaining_budget: float,
        remaining_mass: float,
        allowed_domains: Optional[List[str]] = None,
        name_hint: Optional[str] = None,
        family_filter: Optional[str] = None,
        terrain: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Вибирає найкращий компонент з категорії за зваженою оцінкою
        з урахуванням обмежень бюджету та маси.
        """
        base_cat = self.ALIAS_CATEGORY.get(category, category)
        candidates = list(self._index.get(base_cat, []))
        if not candidates:
            return None

        # Фільтр по доменах
        if allowed_domains:
            ad = set(allowed_domains)
            candidates = [
                c for c in candidates
                if (c.get("domain") or "universal") in ad
                   or (c.get("domain") or "universal") == "universal"
            ]

        # Фільтр по name_hint
        if name_hint:
            hint = name_hint.lower()
            filtered = [
                c for c in candidates if hint in (c.get("name") or "").lower()
            ]
            if filtered:
                candidates = filtered

        # Фільтр по family
        if family_filter:
            filtered = [c for c in candidates if c.get("family") == family_filter]
            if filtered:
                candidates = filtered

        # Terrain-specific: offroad для коліс/шин
        if terrain == "offroad" and base_cat in ("wheel", "tire", "track", "tread"):
            offroad = []
            for c in candidates:
                tags = (c.get("meta") or {}).get("tags") or []
                name_l = (c.get("name") or "").lower()
                if ("off-road" in tags or "offroad" in tags
                        or "terrain_rough" in tags
                        or "off-road" in name_l or "offroad" in name_l):
                    offroad.append(c)
            if offroad:
                candidates = offroad

        # Фільтруємо за бюджетом/масою
        candidates = [c for c in candidates if self._fits(c, remaining_budget, remaining_mass)]
        if not candidates:
            return None

        # Сортуємо за зваженою оцінкою (найвища → перша)
        candidates.sort(
            key=lambda c: self._scorer.calculate_component_score(c, weights),
            reverse=True,
        )
        return candidates[0]

    def _check_connector_compatibility(
        self, motor: Dict, periphery: Dict
    ) -> bool:
        """
        Перевіряє чи мотор сумісний з периферією через connectors.
        Мотор має connector type='axle' → периферія має type='axle_hole'
        (або vice versa через compatible_types).
        """
        motor_connectors = motor.get("connectors") or []
        periphery_connectors = periphery.get("connectors") or []

        for mc in motor_connectors:
            mc_type = mc.get("type", "")
            mc_compatible = mc.get("compatible_types") or []
            for pc in periphery_connectors:
                pc_type = pc.get("type", "")
                pc_compatible = pc.get("compatible_types") or []
                # Пряма сумісність
                if mc_type in pc_compatible or pc_type in mc_compatible:
                    return True
        # Якщо connectors пусті — дозволяємо (багато деталей не мають повних connectors)
        if not motor_connectors or not periphery_connectors:
            return True
        return False

    # ──────────────────────────────────────────────────────────────────
    #  ГОЛОВНИЙ МЕТОД: ПОСЛІДОВНА ГЕНЕРАЦІЯ КОНФІГУРАЦІЇ
    # ──────────────────────────────────────────────────────────────────

    def configure(self, request: ConfigRequest) -> Dict[str, Any]:
        """
        Послідовний конструктор конфігурації.

        Returns:
            dict з ключами: selected, total_price, total_weight,
            remaining_budget, chromosome, warning?
        """
        # ── Валідація
        if not request.functions:
            return {"error": "Будь ласка, оберіть хоча б одну функцію."}
        if request.budget is None or request.weight is None:
            return {"error": "Потрібно вказати бюджет та макс. вагу."}

        weights = self._resolve_weights(request)
        terrain = (request.terrain or "indoor").lower()
        complexity = request.complexityLevel or 2
        size_pref = (request.sizeClass or "medium").lower()

        remaining_budget = float(request.budget)
        remaining_mass = float(request.weight)
        selected: List[Dict] = []
        port_slots_used = 0        # Кількість зайнятих портів хаба
        max_ports = 0              # Загальна кількість портів хаба
        warnings: List[str] = []

        def _add(comp: Dict, qty: int = 1) -> None:
            nonlocal remaining_budget, remaining_mass
            for _ in range(qty):
                selected.append(comp)
                remaining_budget -= comp.get("price") or 0
                remaining_mass -= comp.get("weight") or 0

        # ════════════════════════════════════════════════════════════
        # STEP 1: HUB (CONTROLLER) SELECTION
        # ════════════════════════════════════════════════════════════
        # Бюджетна резервація: Hub + Power мають зайняти не більше 35%
        # щоб залишити достатньо для моторів, периферії та структури
        hub_power_budget = remaining_budget * 0.35
        hub_mass_budget = remaining_mass * 0.3

        hub = self._select_best(
            "controller", weights, hub_power_budget, hub_mass_budget,
            allowed_domains=["universal"],
        )
        if not hub:
            # Якщо немає хаба в 35% бюджету, спробуємо з 50%
            hub = self._select_best(
                "controller", weights, remaining_budget * 0.5, remaining_mass * 0.5,
                allowed_domains=["universal"],
            )
        if not hub:
            # Останній шанс — будь-який доступний
            hub = self._select_best(
                "controller", weights, remaining_budget, remaining_mass,
                allowed_domains=["universal"],
            )
        if not hub:
            return {"error": "Не вдалося знайти підходящий контролер в межах бюджету."}

        max_ports = (hub.get("electronics") or {}).get("ports_count", 4)
        _add(hub)

        # ════════════════════════════════════════════════════════════
        # STEP 2: POWER (БАТАРЕЯ / БЛОК ЖИВЛЕННЯ)
        # ════════════════════════════════════════════════════════════
        # Резервуємо не більше 20% залишку для живлення
        power_budget = remaining_budget * 0.2
        power_mass_budget = remaining_mass * 0.2

        power = self._select_best(
            "power", weights, power_budget, power_mass_budget,
            allowed_domains=["universal"],
        )
        if not power:
            # Спробуємо з більшим бюджетом
            power = self._select_best(
                "power", weights, remaining_budget * 0.4, remaining_mass * 0.4,
                allowed_domains=["universal"],
            )
        if power:
            _add(power)
        else:
            warnings.append("Не знайдено блок живлення — робот може не працювати.")

        # ════════════════════════════════════════════════════════════
        # STEP 2.5: STRUCTURAL FOUNDATION (обов'язкова база/шасі)
        # ════════════════════════════════════════════════════════════
        # Обираємо структурну базу ДО моторів, щоб гарантувати
        # що робот має фундамент для кріплення функціональних деталей.
        # Кількість моторів оцінюємо за запитаними функціями.
        estimated_motors = 0
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()
            if func_l in FUNCTION_MOTOR_MAP:
                sub_map = FUNCTION_MOTOR_MAP[func_l]
                m_count, _ = sub_map.get(sub_choice, list(sub_map.values())[0])
                estimated_motors += m_count

        # Резервуємо порт для сенсорів, якщо вони запитані
        sensor_port_reserve = min(len(request.sensors or []), 2) if request.sensors else 0

        if estimated_motors > 0 and remaining_budget > 10 and remaining_mass > 10:
            struct_base = find_adequate_base(
                self.components, estimated_motors,
                complexity=complexity,
                max_price=remaining_budget * 0.15,
                max_weight=remaining_mass * 0.15,
            )
            if struct_base and self._fits(struct_base, remaining_budget, remaining_mass):
                _add(struct_base)

        # ════════════════════════════════════════════════════════════
        # STEP 3: MOTORS & PERIPHERY (по функціях)
        # ════════════════════════════════════════════════════════════
        motor_periphery_pairs: List[Tuple[Dict, Optional[Dict]]] = []

        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            # Визначаємо тип периферії та кількості
            periphery_cat = None
            motors_needed = 0
            periphery_per_motor = 0

            if func_l in FUNCTION_MOTOR_MAP:
                sub_map = FUNCTION_MOTOR_MAP[func_l]
                motors_needed, periphery_per_motor = sub_map.get(
                    sub_choice, list(sub_map.values())[0]
                )
            if func_l in FUNCTION_PERIPHERY_MAP:
                sub_map_p = FUNCTION_PERIPHERY_MAP[func_l]
                periphery_cat = sub_map_p.get(sub_choice, list(sub_map_p.values())[0])

            domains = FUNCTION_DOMAINS.get(func_l, ["universal"])

            # Підбір моторів
            # Обмежуємо моторів щоб лишити порти для сенсорів
            effective_max_ports = max_ports - sensor_port_reserve
            for _ in range(motors_needed):
                if port_slots_used >= effective_max_ports:
                    warnings.append(
                        f"Порти хаба закінчились ({max_ports}). "
                        f"Не вдалося додати мотор для '{func}'."
                    )
                    break

                motor = self._select_best(
                    "motor", weights, remaining_budget, remaining_mass,
                    allowed_domains=domains,
                )
                if not motor:
                    warnings.append(f"Не знайдено мотор для функції '{func}'.")
                    break

                _add(motor)
                port_slots_used += 1

                # Підбір периферії для цього мотора
                attached_periphery: List[Dict] = []
                if periphery_cat and periphery_per_motor > 0:
                    for _ in range(periphery_per_motor):
                        periph = self._select_best(
                            periphery_cat, weights,
                            remaining_budget, remaining_mass,
                            allowed_domains=domains,
                            terrain=terrain,
                        )
                        if periph and self._check_connector_compatibility(motor, periph):
                            _add(periph)
                            attached_periphery.append(periph)
                        elif periph:
                            # Якщо top candidate не сумісний, спробуємо інших
                            _add(periph)
                            attached_periphery.append(periph)

                    # Для коліс: додаємо шини
                    if periphery_cat == "wheel" and attached_periphery:
                        for _ in attached_periphery:
                            tire = self._select_best(
                                "tire", weights,
                                remaining_budget, remaining_mass,
                                allowed_domains=domains,
                                terrain=terrain,
                            )
                            if tire:
                                _add(tire)

                motor_periphery_pairs.append((motor, attached_periphery[0] if attached_periphery else None))

        # ════════════════════════════════════════════════════════════
        # STEP 3.5: CONTEXT-SPECIFIC ADDITIONS (крила, корпус човна)
        # ════════════════════════════════════════════════════════════
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            # ─── Літак: додаємо парні крила (ліве + праве) ───
            if "літати" in func_l and "літак" in sub_choice:
                fly_domains = ["air", "universal"]
                pairs = 1 if size_pref != "large" else 2

                for _ in range(pairs):
                    wing_left = self._select_best(
                        "structure", weights,
                        remaining_budget, remaining_mass,
                        allowed_domains=fly_domains,
                        name_hint="крило",
                        family_filter="wing_plate",
                    )
                    # Спроба знайти саме ліве крило
                    wing_l = self._select_best(
                        "structure", weights,
                        remaining_budget, remaining_mass,
                        allowed_domains=fly_domains,
                        name_hint="ліва",
                        family_filter="wing_plate",
                    )
                    wing_r = self._select_best(
                        "structure", weights,
                        remaining_budget, remaining_mass,
                        allowed_domains=fly_domains,
                        name_hint="права",
                        family_filter="wing_plate",
                    )
                    if wing_l and self._fits(wing_l, remaining_budget, remaining_mass):
                        _add(wing_l)
                    elif wing_left and self._fits(wing_left, remaining_budget, remaining_mass):
                        _add(wing_left)

                    if wing_r and self._fits(wing_r, remaining_budget, remaining_mass):
                        _add(wing_r)
                    elif wing_left and self._fits(wing_left, remaining_budget, remaining_mass):
                        _add(wing_left)

            # ─── Плавання: додаємо корпус човна ───
            if "плавати" in func_l:
                water_domains = ["water", "universal"]
                boat_hull = self._select_best(
                    "water", weights,
                    remaining_budget, remaining_mass,
                    allowed_domains=water_domains,
                    name_hint="корпус",
                )
                if not boat_hull:
                    # Пробуємо будь-який водний компонент з "човен" у назві
                    boat_hull = self._select_best(
                        "water", weights,
                        remaining_budget, remaining_mass,
                        allowed_domains=water_domains,
                        name_hint="човен",
                    )
                if boat_hull and self._fits(boat_hull, remaining_budget, remaining_mass):
                    _add(boat_hull)

        # Перевірка мінімальної валідності: хоча б 1 мотор (якщо потрібен)
        has_motor = any(c.get("category") == "motor" for c in selected)
        needs_motor = estimated_motors > 0
        if needs_motor and not has_motor:
            return {"error": "Не вдалося підібрати жодного мотора. Збільшіть бюджет або масу."}

        # ════════════════════════════════════════════════════════════
        # STEP 4: SENSORS (по вхідних портах)
        # ════════════════════════════════════════════════════════════
        if request.sensors:
            for sensor_name in request.sensors:
                if port_slots_used >= max_ports:
                    warnings.append(
                        f"Порти хаба закінчились. Не вдалося додати сенсор '{sensor_name}'."
                    )
                    break

                sensor = self._select_best(
                    "sensor", weights, remaining_budget, remaining_mass,
                    allowed_domains=["universal"],
                    name_hint=sensor_name,
                )
                if sensor:
                    _add(sensor)
                    port_slots_used += 1
                else:
                    # Спробуємо будь-який сенсор
                    sensor = self._select_best(
                        "sensor", weights, remaining_budget, remaining_mass,
                        allowed_domains=["universal"],
                    )
                    if sensor:
                        _add(sensor)
                        port_slots_used += 1
                    else:
                        warnings.append(f"Не знайдено сенсор '{sensor_name}'.")

        # ════════════════════════════════════════════════════════════
        # STEP 5: STRUCTURE (каркас, балки, осі, піни)
        # ════════════════════════════════════════════════════════════
        self._add_structure_elements(
            selected, weights, remaining_budget, remaining_mass,
            request, terrain, complexity, size_pref, _add, warnings,
        )

        # ════════════════════════════════════════════════════════════
        # STEP 6: ACCESSORIES (декор, фари)
        # ════════════════════════════════════════════════════════════
        decoration = (request.decorationLevel or "normal").lower()
        if decoration != "minimal":
            lights = self._select_best(
                "accessory", weights, remaining_budget, remaining_mass,
                allowed_domains=["universal", "ground"],
                name_hint="фар",
            )
            if lights:
                qty = 1 if decoration == "normal" else 2
                for _ in range(qty):
                    if self._fits(lights, remaining_budget, remaining_mass):
                        _add(lights)

        # ════════════════════════════════════════════════════════════
        # ФОРМУВАННЯ РЕЗУЛЬТАТУ
        # ════════════════════════════════════════════════════════════
        total_price = sum(c.get("price") or 0 for c in selected)
        total_weight = sum(c.get("weight") or 0 for c in selected)

        # Chromosome для GA: список ID компонентів
        chromosome = [c.get("id") for c in selected]

        result: Dict[str, Any] = {
            "selected": selected,
            "total_price": round(total_price, 2),
            "total_weight": round(total_weight, 1),
            "remaining_budget": round(request.budget - total_price, 2),
            "chromosome": chromosome,
        }

        if warnings:
            result["warning"] = " | ".join(warnings)

        return result

    # ──────────────────────────────────────────────────────────────────
    #  STEP 5 HELPER: СТРУКТУРНІ ЕЛЕМЕНТИ
    # ──────────────────────────────────────────────────────────────────

    def _add_structure_elements(
        self,
        selected: List[Dict],
        weights: Dict[str, float],
        remaining_budget: float,
        remaining_mass: float,
        request: ConfigRequest,
        terrain: str,
        complexity: int,
        size_pref: str,
        _add,
        warnings: List[str],
    ) -> None:
        """Додає структурні елементи (балки, осі, піни, пластини, цеглинки)."""

        # Множники залежно від складності та розміру
        if complexity == 1:
            struct_mult = 0.7
        elif complexity == 3:
            struct_mult = 1.4
        else:
            struct_mult = 1.0

        if size_pref == "small":
            body_mult = 0.7
        elif size_pref == "large":
            body_mult = 1.5
        else:
            body_mult = 1.0

        # Список структурних потреб: (family_filter, кількість)
        # Ми чергуємо блоки та пластини для кращої структури ( Diversity Rule)
        struct_needs = [
            ("brick", max(1, round(2 * body_mult))),
            ("plate", max(1, round(1 * body_mult))),
            ("technic_beam", max(2, round(4 * struct_mult))),
            ("brick", max(1, round(1 * body_mult))),
            ("plate", max(1, round(1 * body_mult))),
            ("axle", max(1, round(2 * struct_mult))),
            ("technic_pin", max(4, round(6 * struct_mult))),
        ]

        # Додаємо маленькі деталі
        small_mult = 1.0 if complexity == 2 else (0.8 if complexity == 1 else 1.2)
        struct_needs.append(("brick", max(2, round(4 * small_mult))))
        struct_needs.append(("plate", max(2, round(4 * small_mult))))

        # Плавання: додаткові корпусні елементи
        has_swim = any("плавати" in f.lower() for f in request.functions)
        if has_swim:
            struct_needs.append(("hull_frame", 1))
            struct_needs.append(("plate", max(3, round(4 * body_mult * struct_mult))))
            struct_needs.append(("brick", max(2, round(3 * body_mult * struct_mult))))

        # Летіння: крила
        has_fly = any("літати" in f.lower() for f in request.functions)
        if has_fly:
            struct_needs.append(("wing_plate", 2))

        # Використовуємо локальний трекінг залишків (параметри — копії,
        # _add() змінює nonlocal змінні в configure(), тому відстежуємо окремо)
        local_budget = remaining_budget
        local_mass = remaining_mass

        for family, qty in struct_needs:
            for _ in range(qty):
                if local_budget <= 0 or local_mass <= 0:
                    break
                comp = self._select_best(
                    "structure", weights, local_budget, local_mass,
                    allowed_domains=["universal"],
                    family_filter=family,
                )
                if comp and self._fits(comp, local_budget, local_mass):
                    _add(comp)
                    local_budget -= comp.get("price") or 0
                    local_mass -= comp.get("weight") or 0

