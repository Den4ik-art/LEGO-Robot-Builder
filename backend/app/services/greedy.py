"""
Жадібний конфігуратор LEGO-робота (Slot-Based).

Послідовно заповнює 8 слотів конфігурації: структурна база,
хаб, живлення, привід, функціональні модулі, сенсори,
структурне підсилення та аксесуари.
"""

from typing import List, Dict, Any, Optional, Set
from app.models.dto import ConfigRequest, PriorityWeights
from app.services.scoring import WeightedScorer
from app.services.constraints import (
    get_complexity_profile,
    get_terrain_domains,
    is_valid_base,
    get_symmetric_wheel_count,
    check_power_balance,
    check_port_count,
    prefer_large_motor,
    ComplexityProfile,
    ALLOWED_WHEEL_COUNTS,
    find_adequate_base,
    compute_stud_area,
    compute_structural_requirement,
)

# Мапа «людських» підтипів на технічні категорії
FUNCTION_TO_CATEGORY_MAP = {
    "їздити": {
        "гусениці": "track",
        "колеса": "wheel",
        "крокуючий": "leg",
    },
    "літати": {
        "квадрокоптер": "propeller",
        "квадрокoptер": "propeller",
        "вертоліт": "propeller",
        "літак": "wing",
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
    "сканувати": "sensor",
}


class GreedyConfigurator:
    """
    Slot-Based Greedy Configurator v3.0.

    Заповнює функціональні слоти послідовно, гарантуючи структурну
    цілісність та логічну коректність конфігурації.
    """

    # Псевдо-категорії → базова категорія
    ALIAS_CATEGORY = {
        "wing": "structure",
        "wing_plate": "structure",
        "wheel_offroad": "wheel",
        "tire_offroad": "tire",
    }

    def __init__(self, components: List[Dict]):
        self.components = components
        self._normalize_components()
        self.component_map = self._build_component_map(self.components)
        self._current_terrain: str = "indoor"
        self._scorer = WeightedScorer(self.components)
        self._current_weights: Dict[str, float] = WeightedScorer.DEFAULT_WEIGHTS.copy()

    # ════════════════════════════════════════════════════════════════
    #  НОРМАЛІЗАЦІЯ
    # ════════════════════════════════════════════════════════════════

    def _normalize_components(self) -> None:
        """Додаємо дефолтні значення для полів."""
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

            # family
            if not comp.get("family"):
                fam = self._infer_family(comp)
                if fam:
                    comp["family"] = fam

            # safety defaults
            if "geometry" not in comp:
                comp["geometry"] = {}
            if "scores" not in comp:
                comp["scores"] = {}
            if "connectors" not in comp:
                comp["connectors"] = []
            if "roles" not in comp:
                comp["roles"] = []

    def _infer_family(self, comp: Dict) -> Optional[str]:
        """Евристика для визначення сімейства компонента."""
        name = (comp.get("name") or "").lower()
        cat = comp.get("category", "")

        if cat == "structure":
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

    # ════════════════════════════════════════════════════════════════
    #  ІНДЕКСАЦІЯ
    # ════════════════════════════════════════════════════════════════

    def _build_component_map(self, components: List[Dict]) -> Dict[str, List[Dict]]:
        component_map: Dict[str, List[Dict]] = {}
        for comp in components:
            category = comp.get("category", "unknown")
            component_map.setdefault(category, []).append(comp)
        return component_map

    # ════════════════════════════════════════════════════════════════
    #  ВАГИ
    # ════════════════════════════════════════════════════════════════

    def _get_weights_from_request(self, request: ConfigRequest) -> Dict[str, float]:
        eco_mode = bool(request.eco_mode) if request.eco_mode else False
        if request.weights is not None:
            w = {
                "speed": request.weights.speed,
                "force": request.weights.force,
                "economy": request.weights.economy,
                "endurance": request.weights.endurance,
                "eco": request.weights.eco,
            }
            if eco_mode:
                from app.services.scoring import WeightedScorer
                w = WeightedScorer.apply_eco_mode(w)
            return w
        return self._scorer.get_weights_from_priority(request.priority, eco_mode=eco_mode)

    # ════════════════════════════════════════════════════════════════
    #  ФІЛЬТРИ та ВИБІР КОМПОНЕНТІВ
    # ════════════════════════════════════════════════════════════════

    def _filter_by_domain(self, candidates: List[Dict], allowed_domains: List[str]) -> List[Dict]:
        """Фільтрація по доменам з урахуванням універсальних компонентів."""
        allowed = set(allowed_domains or [])
        if not allowed:
            return candidates
        result: List[Dict] = []
        for c in candidates:
            dom = c.get("domain", "universal") or "universal"
            if dom == "universal" or dom in allowed:
                result.append(c)
        return result or []

    def _filter_by_role(self, candidates: List[Dict], category: str, role: Optional[str]) -> List[Dict]:
        """Фільтрує кандидатів за роллю."""
        if not role:
            return candidates

        if category == "structure":
            def family(c): return c.get("family")
            def size(c): return (c.get("geometry") or {}).get("size_class") or "medium"

            role_filters = {
                "body_plate": lambda c: family(c) in ("plate", "frame", "wing_plate", "hull_frame") and size(c) in ("medium", "large"),
                "body_brick": lambda c: family(c) in ("brick", "panel", "hull_frame") and size(c) in ("medium", "large"),
                "beam": lambda c: family(c) == "technic_beam",
                "axle": lambda c: family(c) == "axle" or any(conn.get("type") == "axle" for conn in c.get("connectors", []) or []),
                "pin": lambda c: family(c) == "technic_pin" or any(conn.get("type") == "pin" for conn in c.get("connectors", []) or []),
                "gear": lambda c: family(c) == "gear",
                "small_brick": lambda c: family(c) == "brick" and size(c) == "small",
                "small_plate": lambda c: family(c) == "plate" and size(c) == "small",
                "small_detail": lambda c: size(c) == "small",
                "kit": lambda c: "набір" in (c.get("name") or "").lower() or "kit" in (c.get("name") or "").lower(),
                "gearbox": lambda c: "редуктор" in (c.get("name") or "").lower() or "gearbox" in (c.get("name") or "").lower() or family(c) == "gear",
                "wing": lambda c: family(c) == "wing_plate" or "кри" in (c.get("name") or "").lower(),
                "hull": lambda c: family(c) == "hull_frame" or "корпус" in (c.get("name") or "").lower() or "рама" in (c.get("name") or "").lower(),
                "base": lambda c: is_valid_base(c),
            }

            filter_fn = role_filters.get(role)
            if filter_fn:
                filtered = [c for c in candidates if filter_fn(c)]
                return filtered or candidates

        if category == "accessory" and role == "lights":
            filtered = [c for c in candidates if any(kw in (c.get("name") or "").lower() for kw in ("фар", "light", "led"))]
            return filtered or candidates

        return candidates

    def _filter_offroad(self, candidates: List[Dict], category: str) -> List[Dict]:
        """Фільтрує деталі для offroad поверхні."""
        if self._current_terrain != "offroad" or category not in ("wheel", "tire", "track", "tread"):
            return candidates
        offroad: List[Dict] = []
        for c in candidates:
            tags = (c.get("meta") or {}).get("tags") or []
            name_l = (c.get("name") or "").lower()
            if any(kw in tags for kw in ("off-road", "offroad", "terrain_rough")) or "off-road" in name_l or "offroad" in name_l:
                offroad.append(c)
        return offroad if offroad else candidates

    def _find_best_component(
        self,
        category: str,
        priority: str,
        name_hint: str = "",
        role: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        max_price: Optional[float] = None,
        max_weight: Optional[float] = None,
    ) -> Optional[Dict]:
        """Вибір найкращого компонента за зваженою оцінкою."""
        original_category = category
        base_category = self.ALIAS_CATEGORY.get(category, category)

        if original_category in ("wing", "wing_plate") and not role:
            role = "wing"

        candidates = list(self.component_map.get(base_category, []))
        if not candidates:
            return None

        # Offroad фільтр
        candidates = self._filter_offroad(candidates, base_category)

        # Domain фільтр
        if allowed_domains is not None:
            candidates = self._filter_by_domain(candidates, allowed_domains)
            if not candidates:
                return None

        # Role фільтр
        candidates = self._filter_by_role(candidates, base_category, role)

        # Name hint
        if name_hint:
            hint = name_hint.lower()
            filtered = [c for c in candidates if hint in (c.get("name") or "").lower()]
            if filtered:
                candidates = filtered

        # Budget/weight фільтр
        if max_price is not None:
            candidates = [c for c in candidates if (c.get("price") or 0) <= max_price]
        if max_weight is not None:
            candidates = [c for c in candidates if (c.get("weight") or 0) <= max_weight]

        if not candidates:
            return None

        # Зважений скоринг
        scoring_weights = weights if weights else self._current_weights
        sorted_candidates = sorted(
            candidates,
            key=lambda c: self._scorer.calculate_component_score(c, scoring_weights),
            reverse=True,
        )
        return sorted_candidates[0] if sorted_candidates else None

    def _find_best_motor(
        self,
        profile: ComplexityProfile,
        weights: Dict[str, float],
        allowed_domains: Optional[List[str]] = None,
        max_price: Optional[float] = None,
        max_weight: Optional[float] = None,
    ) -> Optional[Dict]:
        """Вибір мотора з урахуванням ComplexityProfile (якість > кількість)."""
        candidates = list(self.component_map.get("motor", []))
        if not candidates:
            return None

        if allowed_domains:
            candidates = self._filter_by_domain(candidates, allowed_domains)
        if max_price is not None:
            candidates = [c for c in candidates if (c.get("price") or 0) <= max_price]
        if max_weight is not None:
            candidates = [c for c in candidates if (c.get("weight") or 0) <= max_weight]
        if not candidates:
            return None

        # Для високої складності — перевагу великим моторам
        if profile.prefer_large_motors:
            large = [c for c in candidates if prefer_large_motor(c)]
            if large:
                candidates = large

        sorted_candidates = sorted(
            candidates,
            key=lambda c: self._scorer.calculate_component_score(c, weights),
            reverse=True,
        )
        return sorted_candidates[0] if sorted_candidates else None

    # ════════════════════════════════════════════════════════════════
    #  ГОЛОВНИЙ МЕТОД:  SLOT-BASED CONFIGURE
    # ════════════════════════════════════════════════════════════════

    def configure(self, request: ConfigRequest) -> Dict[str, Any]:
        """
        Slot-Based конфігурація робота.

        Слоти заповнюються послідовно з гарантією логічної цілісності:
          1. Base  →  2. Hub  →  3. Power  →  4. Drive  →
          5. Functions  →  6. Sensors  →  7. Structure  →  8. Accessories
        """
        if not request.functions or request.budget is None or request.weight is None:
            return {"error": "Будь ласка, заповніть усі обов'язкові параметри."}

        # ── Підготовка параметрів ──
        self._current_terrain = (request.terrain or "indoor").lower()
        weights = self._get_weights_from_request(request)
        self._current_weights = weights
        priority = (request.priority or "").lower()

        complexity = request.complexityLevel or 2
        # Підтримка complexityLevel від 1 до 5
        profile = get_complexity_profile(complexity)
        terrain = self._current_terrain
        size_pref = (request.sizeClass or "medium").lower()
        decoration_level = (request.decorationLevel or "normal").lower()

        remaining_budget = float(request.budget)
        remaining_mass = float(request.weight)
        chosen: List[Dict] = []
        warnings: List[str] = []
        motors_added: List[Dict] = []
        port_slots_used = 0
        max_ports = 4  # default, оновлюється зі Hub

        # Визначаємо допустимі домени
        has_drive = any("їздити" in f.lower() for f in request.functions)
        has_fly = any("літати" in f.lower() for f in request.functions)
        has_swim = any("плавати" in f.lower() for f in request.functions)
        has_manip = any("маніпулювати" in f.lower() for f in request.functions)

        global_domains = ["universal"]
        if has_drive:
            global_domains.append("ground")
        if has_fly:
            global_domains.append("air")
        if has_swim:
            global_domains.append("water")

        def _add(comp: Dict, qty: int = 1) -> bool:
            """Додає компонент, повертає True якщо успішно."""
            nonlocal remaining_budget, remaining_mass
            for _ in range(qty):
                price = comp.get("price") or 0
                weight = comp.get("weight") or 0
                if price > remaining_budget or weight > remaining_mass:
                    return False
                chosen.append(comp)
                remaining_budget -= price
                remaining_mass -= weight
            return True

        def _fits(comp: Dict) -> bool:
            price = comp.get("price") or 0
            weight = comp.get("weight") or 0
            return price <= remaining_budget and weight <= remaining_mass

        # ════════════════════════════════════════════════
        #  SLOT 1: STRUCTURAL BASE  (Scale-Aware Chassis)
        # ════════════════════════════════════════════════
        # Оцінюємо к-ть моторів для масштабного вибору бази
        from app.services.sequential import FUNCTION_MOTOR_MAP
        estimated_motors = 0
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()
            if func_l in FUNCTION_MOTOR_MAP:
                sub_map = FUNCTION_MOTOR_MAP[func_l]
                m_count, _ = sub_map.get(sub_choice, list(sub_map.values())[0])
                estimated_motors += m_count

        # Для водних роботів шукаємо корпус човна як базу
        if has_swim:
            base_comp = self._find_best_component(
                category="water",
                priority=priority,
                allowed_domains=["water", "universal"],
                weights=weights,
                max_price=remaining_budget * 0.2,
                max_weight=remaining_mass * 0.2,
                name_hint="корпус",
            )
            if not base_comp:
                base_comp = self._find_best_component(
                    category="water",
                    priority=priority,
                    allowed_domains=["water", "universal"],
                    weights=weights,
                    max_price=remaining_budget * 0.25,
                    max_weight=remaining_mass * 0.25,
                )
        else:
            # Спочатку пробуємо масштабно-усвідомлений підбір
            base_comp = find_adequate_base(
                self.components, max(estimated_motors, 1),
                complexity=complexity,
                max_price=remaining_budget * 0.15,
                max_weight=remaining_mass * 0.15,
            )
        if not base_comp:
            # Fallback: старий метод — роль-базовий підбір
            base_comp = self._find_best_component(
                category="structure",
                priority=priority,
                role="base",
                allowed_domains=["universal"],
                weights=weights,
                max_price=remaining_budget * 0.25,
                max_weight=remaining_mass * 0.25,
            )
        if not base_comp:
            base_comp = self._find_best_component(
                category="structure",
                priority=priority,
                role="body_plate",
                allowed_domains=["universal"],
                weights=weights,
                max_price=remaining_budget * 0.25,
                max_weight=remaining_mass * 0.25,
            )
        if base_comp:
            _add(base_comp)
        else:
            warnings.append("Не вдалося знайти структурну базу.")

        # ════════════════════════════════════════════════
        #  SLOT 2: CONTROL HUB
        # ════════════════════════════════════════════════
        hub = self._find_best_component(
            category="controller",
            priority=priority,
            allowed_domains=["universal"],
            weights=weights,
            max_price=remaining_budget * 0.35,
            max_weight=remaining_mass * 0.30,
        )
        if not hub:
            hub = self._find_best_component(
                category="controller",
                priority=priority,
                allowed_domains=["universal"],
                weights=weights,
            )
        if not hub:
            return {"error": "Не вдалося знайти контролер (хаб) в межах бюджету."}

        max_ports = (hub.get("electronics") or {}).get("ports_count", 4)
        _add(hub)

        # ════════════════════════════════════════════════
        #  SLOT 3: POWER SOURCE
        # ════════════════════════════════════════════════
        power = self._find_best_component(
            category="power",
            priority=priority,
            allowed_domains=["universal"],
            weights=weights,
            max_price=remaining_budget * 0.20,
            max_weight=remaining_mass * 0.20,
        )
        if not power:
            power = self._find_best_component(
                category="power",
                priority=priority,
                allowed_domains=["universal"],
                weights=weights,
            )
        if power:
            _add(power)
        else:
            warnings.append("Не знайдено блок живлення.")

        # ════════════════════════════════════════════════
        #  SLOT 4: DRIVE MODULE  (Symmetric!)
        # ════════════════════════════════════════════════
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            if "їздити" not in func_l:
                continue

            drive_type = FUNCTION_TO_CATEGORY_MAP["їздити"].get(sub_choice, "wheel")
            func_domains = ["ground", "universal"]

            # Кількість моторів залежно від ComplexityProfile
            motors_for_drive = min(2, profile.max_motors)  # Drive зазвичай 2 мотори
            if profile.level >= 4:
                motors_for_drive = min(4, profile.max_motors)

            # Кількість коліс — симетрична, парна
            raw_wheels = motors_for_drive * 2 if drive_type == "wheel" else motors_for_drive
            wheel_count = get_symmetric_wheel_count(raw_wheels)

            # === Вибираємо ОДИН тип мотора (Quality > Quantity) ===
            motor = self._find_best_motor(
                profile, weights,
                allowed_domains=func_domains,
                max_price=remaining_budget * 0.3,
                max_weight=remaining_mass * 0.3,
            )
            if not motor:
                motor = self._find_best_motor(
                    profile, weights, allowed_domains=func_domains,
                )
            if not motor:
                warnings.append("Не вдалося знайти мотор для 'Їздити'.")
                continue

            # Додаємо мотори
            for _ in range(motors_for_drive):
                if port_slots_used >= max_ports:
                    warnings.append("Порти хабу закінчились.")
                    break
                if _fits(motor):
                    _add(motor)
                    motors_added.append(motor)
                    port_slots_used += 1

            # === Вибираємо ОДИН тип колеса/гусениці (Symmetry Rule) ===
            wheel_comp = self._find_best_component(
                category=drive_type,
                priority=priority,
                allowed_domains=func_domains,
                weights=weights,
                max_price=remaining_budget * 0.25,
                max_weight=remaining_mass * 0.25,
            )
            if wheel_comp:
                _add(wheel_comp, wheel_count)

                # Шини для коліс — той самий тип, та сама кількість
                if drive_type == "wheel":
                    tire_comp = self._find_best_component(
                        category="tire",
                        priority=priority,
                        allowed_domains=func_domains,
                        weights=weights,
                        max_price=remaining_budget * 0.2,
                        max_weight=remaining_mass * 0.2,
                    )
                    if tire_comp:
                        _add(tire_comp, wheel_count)

            # Структурні деталі для приводу
            beam_qty = max(2, round(4 * profile.structure_reinforcement))
            axle_qty = max(1, round(2 * profile.structure_reinforcement))
            pin_qty = max(4, round(6 * profile.structure_reinforcement))

            for role, qty in [("beam", beam_qty), ("axle", axle_qty), ("pin", pin_qty)]:
                comp = self._find_best_component(
                    category="structure", priority=priority, role=role,
                    allowed_domains=["ground", "universal"], weights=weights,
                    max_price=remaining_budget * 0.1,
                    max_weight=remaining_mass * 0.1,
                )
                if comp:
                    actual = min(qty, max(1, int(remaining_budget / max((comp.get("price") or 1), 0.01))))
                    actual = min(actual, qty)
                    for _ in range(actual):
                        if _fits(comp):
                            _add(comp)

            # Шестерні для гусениць або високої стабільності
            if ("гусениці" in sub_choice or priority == "stability") and profile.allow_gearbox:
                gear = self._find_best_component(
                    category="structure", priority=priority, role="gear",
                    allowed_domains=["ground", "universal"], weights=weights,
                )
                if gear and _fits(gear):
                    _add(gear, min(2, round(2 * profile.structure_reinforcement)))

        # ════════════════════════════════════════════════
        #  SLOT 5: FUNCTION MODULES  (Fly / Swim / Manipulate)
        # ════════════════════════════════════════════════
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            # ─── Літати ───
            if "літати" in func_l:
                fly_domains = ["air", "universal"]

                if "квадрокоптер" in sub_choice:
                    motor_qty, prop_qty = 4, 4
                elif "вертоліт" in sub_choice:
                    motor_qty, prop_qty = 1, 1
                elif "літак" in sub_choice:
                    motor_qty, prop_qty = 2, 2
                else:
                    motor_qty, prop_qty = 2, 2

                motor_qty = min(motor_qty, profile.max_motors)

                motor = self._find_best_motor(
                    profile, weights, allowed_domains=fly_domains,
                    max_price=remaining_budget * 0.25,
                    max_weight=remaining_mass * 0.25,
                )
                if motor:
                    for _ in range(motor_qty):
                        if port_slots_used >= max_ports:
                            break
                        if _fits(motor):
                            _add(motor)
                            motors_added.append(motor)
                            port_slots_used += 1

                # Пропелери — завжди додаємо для всіх типів літання
                prop = self._find_best_component(
                    category="propeller", priority=priority,
                    allowed_domains=fly_domains, weights=weights,
                )
                if prop:
                    _add(prop, min(prop_qty, 4))

                # Крила для літака — додаємо пару (ліва + права)
                if "літак" in sub_choice:
                    wing_qty = 2 if size_pref != "large" else 4
                    # Шукаємо ліве крило
                    wing_left = self._find_best_component(
                        category="wing", priority=priority,
                        allowed_domains=fly_domains, weights=weights,
                        name_hint="ліва",
                    )
                    # Шукаємо праве крило
                    wing_right = self._find_best_component(
                        category="wing", priority=priority,
                        allowed_domains=fly_domains, weights=weights,
                        name_hint="права",
                    )
                    pairs = wing_qty // 2
                    for _ in range(pairs):
                        if wing_left and _fits(wing_left):
                            _add(wing_left)
                        if wing_right and _fits(wing_right):
                            _add(wing_right)

                # Структура для літання
                beam = self._find_best_component(
                    "structure", priority, role="beam", allowed_domains=["air", "universal"], weights=weights,
                )
                if beam:
                    _add(beam, max(2, round(2 * profile.structure_reinforcement)))

            # ─── Плавати ───
            elif "плавати" in func_l:
                water_domains = ["water", "universal"]

                motor = self._find_best_motor(
                    profile, weights, allowed_domains=water_domains,
                    max_price=remaining_budget * 0.25,
                    max_weight=remaining_mass * 0.25,
                )
                if motor:
                    for _ in range(2):
                        if port_slots_used >= max_ports:
                            break
                        if _fits(motor):
                            _add(motor)
                            motors_added.append(motor)
                            port_slots_used += 1

                # Водний рушій (гребний гвинт / водомет)
                water_propulsion = self._find_best_component(
                    category="water", priority=priority,
                    allowed_domains=water_domains, weights=weights,
                    name_hint="рушій" if "водомет" in sub_choice else "",
                )
                if water_propulsion:
                    _add(water_propulsion, 2)

                # Додатковий корпус човна (якщо база не з water)
                has_water_base = any(
                    c.get("category") == "water" for c in chosen
                )
                if not has_water_base:
                    hull = self._find_best_component(
                        category="water", priority=priority,
                        allowed_domains=water_domains, weights=weights,
                        name_hint="корпус",
                    )
                    if hull and _fits(hull):
                        _add(hull)

                # Структурні балки для водного каркасу
                beam = self._find_best_component(
                    "structure", priority, role="beam",
                    allowed_domains=["universal"], weights=weights,
                )
                if beam:
                    beam_qty = max(2, round(3 * profile.structure_reinforcement))
                    for _ in range(beam_qty):
                        if _fits(beam):
                            _add(beam)

            # ─── Маніпулювати ───
            elif "маніпулювати" in func_l:
                if not profile.allow_manipulator and profile.level < 2:
                    warnings.append("Маніпулятор недоступний для рівня складності 1.")
                    continue

                manip_type = FUNCTION_TO_CATEGORY_MAP["маніпулювати"].get(sub_choice, "manipulator")
                name_hint = "рука" if "рука" in sub_choice else None

                manip = self._find_best_component(
                    category=manip_type, priority=priority, name_hint=name_hint or "",
                    allowed_domains=["universal"], weights=weights,
                )
                if manip and _fits(manip):
                    _add(manip)

                motor = self._find_best_motor(
                    profile, weights, allowed_domains=["universal"],
                    max_price=remaining_budget * 0.2,
                    max_weight=remaining_mass * 0.2,
                )
                if motor and port_slots_used < max_ports and _fits(motor):
                    _add(motor)
                    motors_added.append(motor)
                    port_slots_used += 1

        # ════════════════════════════════════════════════
        #  SLOT 6: SENSORS  (по ComplexityProfile)
        # ════════════════════════════════════════════════
        sensors_to_add = list(request.sensors) if request.sensors else []

        # Обмежуємо кількість сенсорів за ComplexityProfile
        max_sensors = profile.max_sensors
        sensors_to_add = sensors_to_add[:max_sensors]

        for sensor_name in sensors_to_add:
            if port_slots_used >= max_ports:
                warnings.append(f"Порти закінчились, не вдалось додати сенсор '{sensor_name}'.")
                break

            sensor = self._find_best_component(
                category="sensor", priority=priority, name_hint=sensor_name,
                allowed_domains=["universal"], weights=weights,
                max_price=remaining_budget * 0.15,
                max_weight=remaining_mass * 0.15,
            )
            if not sensor:
                sensor = self._find_best_component(
                    category="sensor", priority=priority,
                    allowed_domains=["universal"], weights=weights,
                )
            if sensor and _fits(sensor):
                _add(sensor)
                port_slots_used += 1
            else:
                warnings.append(f"Не знайдено сенсор '{sensor_name}'.")

        # ════════════════════════════════════════════════
        #  SLOT 7: STRUCTURE REINFORCEMENT
        # ════════════════════════════════════════════════
        self._add_structure_reinforcement(
            chosen, weights, priority, profile, size_pref,
            request, _add, _fits, remaining_budget, remaining_mass, warnings,
        )

        # ════════════════════════════════════════════════
        #  SLOT 8: ACCESSORIES
        # ════════════════════════════════════════════════
        if decoration_level != "minimal":
            lights = self._find_best_component(
                "accessory", priority, role="lights",
                allowed_domains=global_domains, weights=weights,
            )
            if lights and _fits(lights):
                lights_qty = 1 if decoration_level == "normal" else 2
                _add(lights, lights_qty)

        # ════════════════════════════════════════════════
        #  POWER BALANCE CHECK
        # ════════════════════════════════════════════════
        if hub and motors_added:
            if not check_power_balance(hub, motors_added):
                warnings.append("Увага: хаб може не потужний для всіх моторів.")

        # ════════════════════════════════════════════════
        #  DOMAIN FILTERING  (видаляємо невідповідні)
        # ════════════════════════════════════════════════
        def is_forbidden(c: Dict) -> bool:
            cat = (c.get("category") or "").lower()
            dom = (c.get("domain") or "universal").lower()
            if not has_fly and (cat in ("propeller", "wing") or dom == "air"):
                return True
            if not has_swim and cat == "water":
                return True
            return False

        filtered = [c for c in chosen if not is_forbidden(c)]

        # ════════════════════════════════════════════════
        #  ФІНАЛЬНА ВАЛІДАЦІЯ
        # ════════════════════════════════════════════════
        total_cost = sum((c.get("price") or 0) for c in filtered)
        total_weight = sum((c.get("weight") or 0) for c in filtered)

        if total_cost > request.budget:
            return {
                "error": (
                    f"Бюджет перевищено: {total_cost:.2f} > {request.budget:.2f} грн. "
                    f"Спробуйте зменшити складність або оберіть менше функцій."
                )
            }

        if total_weight > request.weight:
            return {
                "error": (
                    f"Вагу перевищено: {total_weight:.2f} > {request.weight:.2f} г. "
                    f"Спробуйте зменшити розмір робота або оберіть легші компоненти."
                )
            }

        # Додаємо unique_id
        final_list = []
        for i, comp in enumerate(filtered):
            comp_copy = dict(comp)
            comp_copy["unique_id"] = f"{comp['id']}-{i}"
            final_list.append(comp_copy)

        return {
            "selected": final_list,
            "total_price": round(total_cost, 2),
            "total_weight": round(total_weight, 2),
            "remaining_budget": round(request.budget - total_cost, 2),
            "warning": " | ".join(warnings) if warnings else None,
        }

    # ════════════════════════════════════════════════════════════════
    #  SLOT 7 HELPER: STRUCTURE REINFORCEMENT
    # ════════════════════════════════════════════════════════════════

    def _add_structure_reinforcement(
        self,
        chosen: List[Dict],
        weights: Dict[str, float],
        priority: str,
        profile: ComplexityProfile,
        size_pref: str,
        request: ConfigRequest,
        _add,
        _fits,
        remaining_budget: float,
        remaining_mass: float,
        warnings: List[str],
    ) -> None:
        """Додає структурні елементи відповідно до ComplexityProfile."""

        # Множник за розміром
        body_mult = {"small": 0.7, "large": 1.5}.get(size_pref, 1.0)
        reinforce = profile.structure_reinforcement

        # Вже маємо base, тому додаємо тільки додаткові елементи
        has_swim = any("плавати" in f.lower() for f in request.functions)
        has_fly = any("літати" in f.lower() for f in request.functions)

        # Основний корпус (якщо ще мало)
        existing_structures = sum(1 for c in chosen if c.get("category") == "structure")
        needed_extra = max(0, profile.min_structure - existing_structures)

        # Пластини для корпусу
        plate = self._find_best_component(
            "structure", priority, role="body_plate",
            allowed_domains=["universal"], weights=weights,
        )
        if plate:
            plate_qty = max(1, round(1 * body_mult * reinforce))
            for _ in range(plate_qty):
                if _fits(plate) and existing_structures + needed_extra > 0:
                    _add(plate)
                    needed_extra -= 1

        # Цеглинки
        brick = self._find_best_component(
            "structure", priority, role="body_brick",
            allowed_domains=["universal"], weights=weights,
        )
        if brick:
            brick_qty = max(1, round(2 * body_mult * reinforce))
            for _ in range(brick_qty):
                if _fits(brick) and needed_extra > 0:
                    _add(brick)
                    needed_extra -= 1

        # Маленькі деталі — лише якщо ще є потреба
        if needed_extra > 0:
            small = self._find_best_component(
                "structure", priority, role="small_detail",
                allowed_domains=["universal"], weights=weights,
            )
            if small:
                for _ in range(min(needed_extra, 4)):
                    if _fits(small):
                        _add(small)

        # Спеціальні структури: крила для літання (тільки для літака, не квадрокоптера)
        if has_fly:
            sub_fly = ""
            for fn in request.functions:
                if "літати" in fn.lower():
                    sub_fly = (request.subFunctions or {}).get(fn, "").lower()
            if "літак" in sub_fly:
                # Додаткові крила з reinforcement (пару вже додали в Slot 5)
                pass
            # Для квадрокоптера/вертольота крила не потрібні

        # Корпус для плавання (якщо ще не додано в Slot 5)
        if has_swim:
            hull_count = sum(1 for c in chosen if c.get("family") == "hull_frame")
            if hull_count < 1:
                hull = self._find_best_component(
                    "structure", priority, role="hull",
                    allowed_domains=["water", "universal"], weights=weights,
                )
                if hull and _fits(hull):
                    _add(hull)

        # Набір деталей (kit)
        if reinforce >= 1.0:
            kit = self._find_best_component(
                "structure", priority, role="kit",
                allowed_domains=["universal"], weights=weights,
            )
            if kit and _fits(kit):
                _add(kit)