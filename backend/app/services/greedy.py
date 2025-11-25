from typing import List, Dict, Any, Optional
from app.models.dto import ConfigRequest

# Мапа "людських" підтипів на технічні категорії
FUNCTION_TO_CATEGORY_MAP = {
    "їздити": {
        "гусениці": "track",
        "колеса": "wheel",
        "крокуючий": "leg",
    },
    "літати": {
        "квадрокоптер": "propeller",
        "квадрокopter": "propeller",
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
    Покращений жадібний конфігуратор LEGO-робота з виправленими проблемами сумісності.
    """

    # псевдо-категорії
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

    # ---------------- НОРМАЛІЗАЦІЯ ---------------- #

    def _normalize_components(self) -> None:
        """Додаємо дефолтні значення для полів, щоб уникнути помилок."""
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

            # safety: geometry/scores/connectors
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

    # ---------------- БАЗОВІ МЕТОДИ ---------------- #

    def _build_component_map(self, components: List[Dict]) -> Dict[str, List[Dict]]:
        component_map: Dict[str, List[Dict]] = {}
        for comp in components:
            category = comp.get("category", "unknown")
            component_map.setdefault(category, []).append(comp)
        return component_map

    # ---------------- ПРІОРИТЕТИ ТА СОРТУВАННЯ ---------------- #

    def _motor_sort_key(self, comp: Dict, priority: str):
        """Ключ сортування для моторів з урахуванням пріоритету."""
        elec = comp.get("electronics") or {}
        rpm = elec.get("rpm_nominal") or 0
        torque = elec.get("torque_nominal_ncm") or 0
        price = comp.get("price") or 0
        weight = comp.get("weight") or 0
        perf = rpm * torque
        p = (priority or "").lower()

        if p == "speed":
            return (rpm, torque, -price)
        if p == "stability":
            return (torque, weight, -price)
        if p == "cheapness":
            return (-price, perf, torque)
        if p == "durability":
            return (weight, torque, -price)
        return (perf, -price)

    # ---------------- ФІЛЬТРИ ---------------- #

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

    def _apply_role_filter(
        self,
        candidates: List[Dict],
        category: str,
        role: Optional[str],
    ) -> List[Dict]:
        """Застосування фільтрів за роллю компонента."""
        if not role:
            return candidates

        # ---- STRUCTURE ----
        if category == "structure":
            def family(c): return c.get("family")
            def geom(c): return (c.get("geometry") or {})
            def size(c):
                g = geom(c)
                return g.get("size_class") or "medium"

            if role == "body_plate":
                filtered = [
                    c for c in candidates
                    if family(c) in ("plate", "frame", "wing_plate", "hull_frame")
                    and size(c) in ("medium", "large")
                ]
                return filtered or candidates

            if role == "body_brick":
                filtered = [
                    c for c in candidates
                    if family(c) in ("brick", "panel", "hull_frame")
                    and size(c) in ("medium", "large")
                ]
                return filtered or candidates

            if role == "beam":
                filtered = [c for c in candidates if family(c) == "technic_beam"]
                return filtered or candidates

            if role == "axle":
                filtered = [
                    c for c in candidates
                    if family(c) == "axle"
                    or any((conn.get("type") == "axle") for conn in c.get("connectors", []) or [])
                ]
                return filtered or candidates

            if role == "pin":
                filtered = [
                    c for c in candidates
                    if family(c) == "technic_pin"
                    or any((conn.get("type") == "pin") for conn in c.get("connectors", []) or [])
                ]
                return filtered or candidates

            if role == "gear":
                filtered = [c for c in candidates if family(c) == "gear"]
                return filtered or candidates

            if role == "small_brick":
                filtered = [
                    c for c in candidates
                    if family(c) == "brick" and size(c) == "small"
                ]
                return filtered or candidates

            if role == "small_plate":
                filtered = [
                    c for c in candidates
                    if family(c) == "plate" and size(c) == "small"
                ]
                return filtered or candidates

            if role == "small_detail":
                filtered = [
                    c for c in candidates
                    if size(c) == "small"
                    and (c.get("primary_role") or "structural") == "structural"
                ]
                return filtered or candidates

            if role == "kit":
                filtered = [
                    c for c in candidates
                    if "набір" in (c.get("name") or "").lower()
                    or "kit" in (c.get("name") or "").lower()
                ]
                return filtered or candidates

            if role == "gearbox":
                filtered = [
                    c for c in candidates
                    if "редуктор" in (c.get("name") or "").lower()
                    or "gearbox" in (c.get("name") or "").lower()
                ]
                if filtered:
                    return filtered
                filtered = [c for c in candidates if family(c) == "gear"]
                return filtered or candidates

            if role == "wing":
                filtered = [
                    c for c in candidates
                    if family(c) == "wing_plate"
                    or "кри" in (c.get("name") or "").lower()
                ]
                return filtered or candidates

            if role == "hull":
                filtered = [
                    c for c in candidates
                    if family(c) == "hull_frame"
                    or "корпус" in (c.get("name") or "").lower()
                    or "рама" in (c.get("name") or "").lower()
                ]
                return filtered or candidates

        # ---- ACCESSORY ----
        if category == "accessory" and role == "lights":
            filtered = []
            for c in candidates:
                n = (c.get("name") or "").lower()
                if "фар" in n or "light" in n or "led" in n:
                    filtered.append(c)
            return filtered or candidates

        return candidates

    # ---------------- ПОКРАЩЕНИЙ ВИБІР КОМПОНЕНТІВ ---------------- #

    def _find_best_component(
        self,
        category: str,
        priority: str,
        name_hint: str = "",
        role: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Покращений метод вибору компонента з гарантією сумісності."""
        original_category = category
        base_category = self.ALIAS_CATEGORY.get(category, category)

        # спеціальна роль для псевдо-категорій
        if original_category in ("wing", "wing_plate") and not role:
            role = "wing"

        candidates = self.component_map.get(base_category, [])
        if not candidates:
            return None

        # Спеціальна обробка offroad-поверхні для рухових елементів
        terrain = getattr(self, "_current_terrain", "indoor")
        if terrain == "offroad" and base_category in ("wheel", "tire", "track", "tread"):
            offroad_candidates: List[Dict] = []
            for c in candidates:
                meta = c.get("meta") or {}
                tags = meta.get("tags") or []
                name_l = (c.get("name") or "").lower()
                if (
                    "off-road" in tags
                    or "offroad" in tags
                    or "terrain_rough" in tags
                    or "off-road" in name_l
                    or "offroad" in name_l
                ):
                    offroad_candidates.append(c)
            if offroad_candidates:
                candidates = offroad_candidates


        p = (priority or "").lower()

        # Фільтрація за доменами
        if allowed_domains is not None:
            candidates = self._filter_by_domain(candidates, allowed_domains)
            if not candidates:
                return None

        # Фільтрація за роллю
        candidates = self._apply_role_filter(candidates, base_category, role)

        # Пошук за назвою
        if name_hint:
            hint = name_hint.lower()
            filtered = [
                c for c in candidates
                if hint in (c.get("name") or "").lower()
            ]
            if filtered:
                candidates = filtered

        # Спеціальний фільтр для крил
        if original_category in ("wing", "wing_plate") and not role:
            wings = [
                c for c in candidates
                if "кри" in (c.get("name") or "").lower()
                or (c.get("family") == "wing_plate")
            ]
            if wings:
                candidates = wings

        if not candidates:
            return None

        # Спеціальна обробка offroad-поверхні для рухових елементів
        terrain = getattr(self, "_current_terrain", "indoor")
        if terrain == "offroad" and base_category in ("wheel", "tire", "track", "tread"):
            offroad_candidates: List[Dict] = []
            for c in candidates:
                meta = c.get("meta") or {}
                tags = meta.get("tags") or []
                name_l = (c.get("name") or "").lower()
                if (
                    "off-road" in tags
                    or "offroad" in tags
                    or "terrain_rough" in tags
                    or "off-road" in name_l
                    or "offroad" in name_l
                ):
                    offroad_candidates.append(c)
            if offroad_candidates:
                candidates = offroad_candidates


        # ---- Мотори ----
        if base_category == "motor":
            sorted_candidates = sorted(
                candidates,
                key=lambda c: self._motor_sort_key(c, p),
                reverse=True,
            )
            return sorted_candidates[0]

        # ---- Структурні деталі ----
        if base_category == "structure":
            def struct_key(c: Dict):
                geom = c.get("geometry") or {}
                scores = c.get("scores") or {}

                stud_len = geom.get("stud_length") or 0
                stud_wid = geom.get("stud_width") or 0
                studs_total = stud_len * stud_wid

                strength = scores.get("structural_strength") or 0
                cost_eff = scores.get("cost_efficiency") or 0
                conn_vers = scores.get("connection_versatility") or 0
                price = c.get("price") or 0

                if not any([studs_total, strength, cost_eff, conn_vers]):
                    if p == "cheapness":
                        return (-price,)
                    return (-price,)

                if p == "cheapness":
                    return (cost_eff, strength, conn_vers, -price)
                if p == "durability":
                    return (strength, conn_vers, studs_total, -price)
                return (strength, conn_vers, studs_total, -price)

            sorted_candidates = sorted(
                candidates,
                key=struct_key,
                reverse=True,
            )
            return sorted_candidates[0] if sorted_candidates else None

        # ---- Загальний випадок ----
        def general_score(c: Dict):
            scores = c.get("scores") or {}
            price = c.get("price") or 0
            weight = c.get("weight") or 0

            if p == "cheapness":
                return (-price, scores.get("cost_efficiency") or 0)
            if p == "durability":
                return (scores.get("structural_strength") or 0, -price)
            if p == "speed":
                elec = c.get("electronics") or {}
                rpm = elec.get("rpm_nominal") or 0
                return (rpm, -price)
            if p == "stability":
                elec = c.get("electronics") or {}
                torque = elec.get("torque_nominal_ncm") or 0
                return (torque, weight, -price)
            return (-price,)

        sorted_candidates = sorted(
            candidates,
            key=general_score,
            reverse=True,
        )
        return sorted_candidates[0] if sorted_candidates else None

    # ---------------- ПОКРАЩЕНИЙ BLUEPRINT ---------------- #

    def _build_blueprint(self, request: ConfigRequest) -> Dict[str, Dict[str, Any]]:
        """Покращений blueprint з гарантією сумісності компонентів."""
        bp: Dict[str, Dict[str, Any]] = {}

        def add(key: str, qty: int = 1, name_hint: Optional[str] = None, domains: Optional[List[str]] = None):
            if key not in bp:
                bp[key] = {
                    "quantity": 0,
                    "name_hint": None,
                    "domains": domains or ["universal", "ground", "air", "water"],
                }
            bp[key]["quantity"] += qty
            if name_hint and not bp[key].get("name_hint"):
                bp[key]["name_hint"] = name_hint
            if domains is not None:
                bp[key]["domains"] = domains

        # ---------- Параметри користувача ---------- #
        size_pref = (request.sizeClass or "medium").lower()
        complexity = request.complexityLevel or 2
        terrain = (request.terrain or "indoor").lower()
        decoration_level = (request.decorationLevel or "normal").lower()

        # ---------- Коефіцієнти кількості деталей ---------- #
        if complexity == 1:
            struct_mult = 0.7
            gear_mult = 0.5
            small_mult = 0.8
        elif complexity == 3:
            struct_mult = 1.4
            gear_mult = 1.5
            small_mult = 1.2
        else:  # 2
            struct_mult = 1.0
            gear_mult = 1.0
            small_mult = 1.0

        if size_pref == "small":
            body_mult = 0.7
        elif size_pref == "large":
            body_mult = 1.5
        else:
            body_mult = 1.0

        # ---------- Базові елементи для будь-якого робота ---------- #
        add("controller", 1, domains=["universal"])
        add("power", 1, domains=["universal"])

        base_body_plate = max(1, round(1 * body_mult))
        base_body_brick = max(1, round(2 * body_mult))

        add("structure:body_plate", base_body_plate, domains=["universal"])
        add("structure:body_brick", base_body_brick, domains=["universal"])

        base_kits = max(1, round(1 * struct_mult))
        add("structure:kit", base_kits, domains=["universal"])

        small_brick_qty = max(2, round(4 * small_mult))
        small_plate_qty = max(2, round(4 * small_mult))
        small_detail_qty = max(2, round(4 * small_mult))

        add("structure:small_brick", small_brick_qty, domains=["universal"])
        add("structure:small_plate", small_plate_qty, domains=["universal"])
        add("structure:small_detail", small_detail_qty, domains=["universal"])

        # ---------- Функції робота ---------- #
        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            # ---- Їздити ---- #
            if "їздити" in func_l:
                drive_type = FUNCTION_TO_CATEGORY_MAP["їздити"].get(sub_choice, "wheel")

                motors_qty = 2
                wheels_qty = 4

                if terrain == "offroad":
                    motors_qty = 2
                    wheels_qty = 4

                add("motor", motors_qty, domains=["ground", "universal"])
                add(drive_type, wheels_qty, domains=["ground"])

                # Колеса + шини завжди разом
                if drive_type == "wheel":
                    add("tire", wheels_qty, domains=["ground"])

                beam_qty = max(2, round(4 * struct_mult))
                axle_qty = max(1, round(2 * struct_mult))
                pin_qty = max(4, round(6 * struct_mult))

                add("structure:beam", beam_qty, domains=["ground", "universal"])
                add("structure:axle", axle_qty, domains=["ground", "universal"])
                add("structure:pin", pin_qty, domains=["ground", "universal"])

                if "гусениці" in sub_choice or (request.priority or "").lower() == "stability":
                    gearbox_qty = max(1, round(1 * gear_mult))
                    gear_qty = max(1, round(2 * gear_mult))
                    add("structure:gearbox", gearbox_qty, domains=["ground", "universal"])
                    add("structure:gear", gear_qty, domains=["ground", "universal"])

                if decoration_level != "minimal":
                    lights_qty = 1 if decoration_level == "normal" else 2
                    add("accessory:lights", lights_qty, domains=["ground", "universal"])

            # ---- Літати ---- #
            elif "літати" in func_l:
                fly_type = FUNCTION_TO_CATEGORY_MAP["літати"].get(sub_choice, "propeller")

                if "квадрокоптер" in sub_choice:
                    motors_qty = 4
                    props_qty = 4
                    add("motor", motors_qty, domains=["air", "universal"])
                    add(fly_type, props_qty, domains=["air"])
                elif "вертоліт" in sub_choice:
                    motors_qty = 1
                    props_qty = 1
                    add("motor", motors_qty, domains=["air", "universal"])
                    add(fly_type, props_qty, domains=["air"])
                elif "літак" in sub_choice:
                    motors_qty = 2
                    add("motor", motors_qty, domains=["air", "universal"])
                    add("wing", 2, domains=["air"])
                    add(
                        "structure:body_plate",
                        max(1, round(1 * body_mult)),
                        name_hint="фюзеляж",
                        domains=["air", "universal"],
                    )
                    add("propeller", 2, name_hint="турб", domains=["air", "universal"])
                else:
                    motors_qty = 2
                    props_qty = 2
                    add("motor", motors_qty, domains=["air", "universal"])
                    add(fly_type, props_qty, domains=["air"])

                add("structure:beam", max(2, round(2 * struct_mult)), domains=["air", "universal"])
                add("structure:pin", max(2, round(4 * struct_mult)), domains=["air", "universal"])

            # ---- Маніпулювати ---- #
            elif "маніпулювати" in func_l:
                manip_type = FUNCTION_TO_CATEGORY_MAP["маніпулювати"].get(sub_choice, "manipulator")
                name_hint = "рука" if "рука" in sub_choice else None

                add(manip_type, 1, name_hint=name_hint, domains=["universal"])
                add("motor", 1, domains=["universal"])

                add("structure:beam", max(3, round(3 * struct_mult)), domains=["universal"])
                add("structure:pin", max(4, round(6 * struct_mult)), domains=["universal"])
                add("structure:axle", max(2, round(2 * struct_mult)), domains=["universal"])

            # ---- Плавати ---- #
            elif "плавати" in func_l:
                water_type = FUNCTION_TO_CATEGORY_MAP["плавати"].get(sub_choice, "water")

                add("motor", 2, domains=["water", "universal"])
                add(water_type, 2, domains=["water"])

                # ОБОВ'ЯЗКОВІ елементи корпусу човна
                hull_plate_qty = max(3, round(4 * body_mult * struct_mult))
                hull_brick_qty = max(2, round(3 * body_mult * struct_mult))
                
                add("structure:body_plate", hull_plate_qty, domains=["water", "universal"])
                add("structure:body_brick", hull_brick_qty, domains=["water", "universal"])
                add("structure:hull", 1, domains=["water", "universal"])
                
                add("structure:beam", max(4, round(6 * struct_mult)), domains=["water", "universal"])
                add("structure:axle", max(2, round(2 * struct_mult)), domains=["water", "universal"])
                add("structure:pin", max(4, round(6 * struct_mult)), domains=["water", "universal"])

        # ---- Сенсори ---- #
        if request.sensors:
            add("sensor", len(request.sensors), domains=["universal"])

        return bp

    # ---------------- НОВІ МЕТОДИ ДЛЯ ГАРАНТІЇ СУМІСНОСТІ ---------------- #

    def _ensure_wheel_tire_compatibility(self, components: List[Dict]) -> List[Dict]:
        """Гарантує, що кожна шина має відповідне колесо і навпаки."""
        wheels = [c for c in components if c.get("category") == "wheel"]
        tires = [c for c in components if c.get("category") == "tire"]
        
        # Якщо є шини, але немає коліс - додаємо колеса
        if tires and not wheels:
            wheel_comp = self._find_best_component(
                category="wheel",
                priority="balanced",
                allowed_domains=["ground", "universal"],
            )
            if wheel_comp:
                components.extend([wheel_comp] * len(tires))
        
        # Якщо є колеса, але немає шин - додаємо шини
        if wheels and not tires:
            tire_comp = self._find_best_component(
                category="tire", 
                priority="balanced",
                allowed_domains=["ground", "universal"],
            )
            if tire_comp:
                components.extend([tire_comp] * len(wheels))
        
        return components

    def _ensure_hull_components(self, components: List[Dict], request: ConfigRequest) -> List[Dict]:
        """Гарантує наявність корпусних елементів та основи (hull) для водних роботів."""
        # Вже обрані корпусні елементи / основа
        hull_components: List[Dict] = []
        for c in components:
            if c.get("is_base"):
                hull_components.append(c)
                continue
            family = c.get("family")
            category = c.get("category")
            name_l = (c.get("name") or "").lower()
            if family in ["hull_frame", "body_plate", "body_brick"]:
                hull_components.append(c)
            elif category == "water" and any(k in name_l for k in ["корпус", "hull", "човн", "човна"]):
                hull_components.append(c)

        # Якщо немає базового корпусу для плавучості - підбираємо з категорії water
        has_base_hull = any(c.get("is_base") or c.get("category") == "water" for c in hull_components)
        if not has_base_hull:
            base_hull = self._find_best_component(
                category="water",
                priority=request.priority or "stability",
                name_hint="корпус",
                allowed_domains=["water"],
            )
            if base_hull:
                components.append(base_hull)
                hull_components.append(base_hull)

        # Додаємо додаткові корпусні елементи, якщо їх замало
        if len(hull_components) < 3:
            extra_hull = self._find_best_component(
                category="structure",
                priority=request.priority or "stability",
                role="body_plate",
                allowed_domains=["water", "universal"],
            )
            if extra_hull:
                components.append(extra_hull)

        return components


    def _ensure_component_compatibility(self, components: List[Dict], request: ConfigRequest) -> List[Dict]:
        """Головний метод гарантії сумісності всіх компонентів."""
        components = self._ensure_wheel_tire_compatibility(components)
        
        # Перевіряємо чи є водні функції
        has_water = any("плавати" in f.lower() for f in request.functions)
        if has_water:
            components = self._ensure_hull_components(components, request)
            
        return components

    def configure(self, request: ConfigRequest) -> Dict[str, Any]:
        """Покращений основний метод конфігурації з кращою обробкою помилок."""
        if not request.functions or request.budget is None or request.weight is None:
            return {"error": "Будь ласка, заповніть усі обов'язкові параметри."}

        # зберігаємо поточний тип поверхні для подальшого підбору компонентів
        try:
            self._current_terrain = (request.terrain or "indoor").lower()
        except Exception:
            self._current_terrain = "indoor"

        try:
            blueprint = self._build_blueprint(request)
        except Exception as e:
            return {"error": f"Помилка при плануванні конфігурації: {str(e)}"}

        chosen_components: List[Dict] = []
        current_cost = 0.0
        current_weight = 0.0
        priority = (request.priority or "").lower()

        has_fly = any("літати" in f.lower() for f in request.functions)
        has_swim = any("плавати" in f.lower() for f in request.functions)

        try:
            for key, info in blueprint.items():
                quantity = info.get("quantity", 0)
                if quantity <= 0:
                    continue

                if ":" in key:
                    base_category, role = key.split(":", 1)
                else:
                    base_category, role = key, None

                domains = info.get("domains") or ["universal", "ground", "air", "water"]
                name_hint = info.get("name_hint") or ""

                # Спеціальна обробка сенсорів
                if base_category == "sensor":
                    for sensor_name in request.sensors:
                        component = self._find_best_component(
                            category=base_category,
                            priority=priority,
                            name_hint=sensor_name,
                            role=None,
                            allowed_domains=["universal"],
                        )
                        if not component:
                            # Спробуємо знайти будь-який сенсор як запасний варіант
                            component = self._find_best_component(
                                category=base_category,
                                priority=priority,
                                allowed_domains=["universal"],
                            )
                            if not component:
                                continue
                        
                        chosen_components.append(component)
                        current_cost += component.get("price") or 0
                        current_weight += component.get("weight") or 0
                    continue

                component = self._find_best_component(
                    category=base_category,
                    priority=priority,
                    name_hint=name_hint,
                    role=role,
                    allowed_domains=domains,
                )
                
                if not component:
                    # Спробуємо знайти компонент без доменних обмежень
                    component = self._find_best_component(
                        category=base_category,
                        priority=priority,
                        name_hint=name_hint,
                        role=role,
                        allowed_domains=None,
                    )
                    if not component:
                        raise Exception(f"Не вдалося знайти компонент: {key}")

                for _ in range(quantity):
                    chosen_components.append(component)
                    current_cost += component.get("price") or 0
                    current_weight += component.get("weight") or 0

        except Exception as e:
            return {"error": f"Помилка підбору компонентів: {str(e)}"}

        # ---- ГАРАНТІЯ СУМІСНОСТІ КОМПОНЕНТІВ ----
        chosen_components = self._ensure_component_compatibility(chosen_components, request)

        # ---- Фільтрація недоречних доменів ----
        def is_forbidden(c: Dict) -> bool:
            cat = (c.get("category") or "").lower()
            dom = (c.get("domain") or "universal").lower()
            if not has_fly and (cat in ("propeller", "wing") or dom == "air"):
                return True
            if not has_swim and (cat == "water" or dom == "water"):
                return False
            return False

        filtered_components = [c for c in chosen_components if not is_forbidden(c)]

        # ---- Фінальний перерахунок ----
        current_cost = sum((c.get("price") or 0) for c in filtered_components)
        current_weight = sum((c.get("weight") or 0) for c in filtered_components)

        # Перевірка бюджету та ваги
        if current_cost > request.budget:
            return {
                "error": (
                    f"Бюджет перевищено: {current_cost:.2f} > {request.budget:.2f} грн. "
                    f"Спробуйте зменшити складність або оберіть менше функцій."
                )
            }

        if current_weight > request.weight:
            return {
                "error": (
                    f"Вагу перевищено: {current_weight:.2f} > {request.weight:.2f} г. "
                    f"Спробуйте зменшити розмір робота або оберіть легші компоненти."
                )
            }

        # Створення фінального списку з унікальними ID
        final_list = []
        for i, comp in enumerate(filtered_components):
            comp_copy = dict(comp)
            comp_copy["unique_id"] = f"{comp['id']}-{i}"
            final_list.append(comp_copy)

        return {
            "selected": final_list,
            "total_price": round(current_cost, 2),
            "total_weight": round(current_weight, 2),
            "remaining_budget": round(request.budget - current_cost, 2),
            "warning": "Конфігурація успішно створена з гарантією сумісності компонентів!" if has_swim else None
        }