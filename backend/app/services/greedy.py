# backend/app/services/greedy.py

from typing import List, Dict, Any, Optional
from app.models.dto import ConfigRequest

# Мапа “людських” підтипів на технічні категорії
FUNCTION_TO_CATEGORY_MAP = {
    "їздити": {
        "гусениці": "track",
        "колеса": "wheel",
        "крокуючий": "leg",
    },
    "літати": {
        "квадрокоптер": "propeller",
        "квадрокoрter": "propeller",
        "вертоліт": "propeller",
        "літак": "wing",  # Літак → псевдо-категорія wing
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
    Жадібний конфігуратор LEGO-робота під lego_components.json.
    Працює як з “простим” JSON (id, name, category, price, weight, image),
    так і з розширеним (geometry, scores, domain, family тощо — якщо зʼявляться).
    """

    # псевдо-категорії, які насправді сидять у інших категоріях
    ALIAS_CATEGORY = {
        "wing": "structure",
        "wing_plate": "structure",
    }

    def __init__(self, components: List[Dict]):
        self.components = components
        # Попередній нормалізуючий прогін: domain/family/поля
        self._normalize_components()
        self.component_map = self._build_component_map(self.components)

    # ---------------- НОРМАЛІЗАЦІЯ ---------------- #

    def _normalize_components(self) -> None:
        """
        Додаємо дефолтні значення domain, family (по назві), щоб фільтри
        працювали навіть із простим json.
        """
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

            # family (якщо немає – пробуємо вгадати по назві)
            if not comp.get("family"):
                fam = self._infer_family(comp)
                if fam:
                    comp["family"] = fam

            # safety: geometry/scores можуть бути відсутні
            if "geometry" not in comp:
                comp["geometry"] = {}
            if "scores" not in comp:
                comp["scores"] = {}
            if "connectors" not in comp:
                comp["connectors"] = []

    def _infer_family(self, comp: Dict) -> Optional[str]:
        """
        Дуже проста евристика по назві, щоб заповнити family
        (потрібно для ролей body_plate / beam / axle / pin / gear / wing_plate тощо).
        """
        name = (comp.get("name") or "").lower()
        cat = comp.get("category", "")

        if cat == "structure":
            # крила
            if "кри" in name or "пластина-крило" in name or "клин (крило)" in name:
                return "wing_plate"

            # пластини
            if "пластина" in name or "plate" in name:
                return "plate"

            # цеглинки
            if "цегл" in name or "brick" in name:
                return "brick"

            # панелі
            if "панель" in name or "panel" in name:
                return "panel"

            # технік-балки / піни / осі / шестерні
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

            # шестерні без слова technic
            if "шестерн" in name or "gear" in name:
                return "gear"

        return None

    # ---------------- БАЗА ---------------- #

    def _build_component_map(self, components: List[Dict]) -> Dict[str, List[Dict]]:
        component_map: Dict[str, List[Dict]] = {}
        for comp in components:
            category = comp.get("category", "unknown")
            component_map.setdefault(category, []).append(comp)
        return component_map

    # ---------------- ПРІОРИТЕТИ ---------------- #

    def _motor_sort_key(self, comp: Dict, priority: str):
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
        """
        Фільтрація по domain:
        - 'universal' завжди проходить;
        - якщо allowed_domains порожній → нічого не фільтруємо.
        """
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
        if not role:
            return candidates

        # ---- STRUCTURE ----
        if category == "structure":
            def family(c): return c.get("family")
            def geom(c): return (c.get("geometry") or {})
            def size(c):
                g = geom(c)
                return g.get("size_class") or "medium"

            # основні пластини / рами (у т.ч. крильові)
            if role == "body_plate":
                filtered = [
                    c for c in candidates
                    if family(c) in ("plate", "frame", "wing_plate")
                    and size(c) in ("medium", "large")
                ]
                return filtered or candidates

            # обʼємні цеглинки / панелі
            if role == "body_brick":
                filtered = [
                    c for c in candidates
                    if family(c) in ("brick", "panel")
                    and size(c) in ("medium", "large")
                ]
                return filtered or candidates

            # технік-балки
            if role == "beam":
                filtered = [c for c in candidates if family(c) == "technic_beam"]
                return filtered or candidates

            # осі
            if role == "axle":
                filtered = [
                    c for c in candidates
                    if family(c) == "axle"
                    or any((conn.get("type") == "axle") for conn in c.get("connectors", []) or [])
                ]
                return filtered or candidates

            # піни
            if role == "pin":
                filtered = [
                    c for c in candidates
                    if family(c) == "technic_pin"
                    or any((conn.get("type") == "pin") for conn in c.get("connectors", []) or [])
                ]
                return filtered or candidates

            # шестерні
            if role == "gear":
                filtered = [c for c in candidates if family(c) == "gear"]
                return filtered or candidates

            # дрібні цеглинки / пластинки / деталі
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

            # набори
            if role == "kit":
                filtered = [
                    c for c in candidates
                    if "набір" in (c.get("name") or "").lower()
                    or "kit" in (c.get("name") or "").lower()
                ]
                return filtered or candidates

            # редуктор
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

            # крила / крилові пластини
            if role == "wing":
                filtered = [
                    c for c in candidates
                    if family(c) == "wing_plate"
                    or "кри" in (c.get("name") or "").lower()
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

    # ---------------- ВИБІР КОМПОНЕНТА ---------------- #

    def _find_best_component(
        self,
        category: str,
        priority: str,
        name_hint: str = "",
        role: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """
        Підбирає кращий компонент з урахуванням:
        - псевдо-категорій (wing → structure + роль wing),
        - доменів (ground/air/water/universal),
        - ролі (beam, body_plate тощо),
        - пріоритету (speed/cheapness/stability/durability).
        """

        original_category = category
        base_category = self.ALIAS_CATEGORY.get(category, category)

        # спеціальна роль для псевдо-категорій
        if original_category in ("wing", "wing_plate") and not role:
            role = "wing"

        candidates = self.component_map.get(base_category, [])
        if not candidates:
            return None

        p = (priority or "").lower()

        if allowed_domains is not None:
            candidates = self._filter_by_domain(candidates, allowed_domains)
            if not candidates:
                return None

        # рольові фільтри по структурі / аксесуарам
        candidates = self._apply_role_filter(candidates, base_category, role)

        # hint по назві
        if name_hint:
            hint = name_hint.lower()
            filtered = [
                c for c in candidates
                if hint in (c.get("name") or "").lower()
            ]
            if filtered:
                candidates = filtered

        # спец-фільтр по крилам, якщо ще треба
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

                # якщо все по нулях – просто дивимось на ціну
                if not any([studs_total, strength, cost_eff, conn_vers]):
                    if p == "cheapness":
                        return (-price,)
                    return (-price,)

                if p == "cheapness":
                    return (cost_eff, strength, conn_vers, -price)
                if p == "durability":
                    return (strength, conn_vers, studs_total, -price)
                # speed / stability → хороша несуча деталь
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

    # ---------------- BLUEPRINT ---------------- #

    def _build_blueprint(self, request: ConfigRequest) -> Dict[str, Dict[str, Any]]:
        """
        blueprint: key -> "category[:role]"
        value -> { "quantity": int, "name_hint": Optional[str], "domains": List[str] }
        """

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

        size_pref = (request.sizeClass or "medium").lower()      # small|medium|large
        complexity = request.complexityLevel or 2                # 1/2/3
        terrain = (request.terrain or "indoor").lower()          # indoor|outdoor_flat|offroad|water_pool
        decoration_level = (request.decorationLevel or "normal").lower()  # minimal|normal|rich

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

        # контролер / живлення
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

                # Пара коліс + шин для машин
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

                # квадрокоптер / вертоліт
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
                # літак — крила+фюзеляж+турбіни
                elif "літак" in sub_choice:
                    motors_qty = 2
                    add("motor", motors_qty, domains=["air", "universal"])

                    # крила як псевдо-категорія 'wing' → structure з роллю wing
                    add("wing", 2, domains=["air"])
                    # фюзеляж / корпус
                    add(
                        "structure:body_plate",
                        max(1, round(1 * body_mult)),
                        name_hint="фюзеляж",
                        domains=["air", "universal"],
                    )
                    # турбіни (propeller з hint "турб")
                    add("propeller", 2, name_hint="турб", domains=["air", "universal"])
                else:
                    # дефолт: простий літальний апарат на пропелерах
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

                # для маніпуляторів – більше технік деталей
                add("structure:beam", max(3, round(3 * struct_mult)), domains=["universal"])
                add("structure:pin", max(4, round(6 * struct_mult)), domains=["universal"])
                add("structure:axle", max(2, round(2 * struct_mult)), domains=["universal"])

            # ---- Плавати ---- #
            elif "плавати" in func_l:
                water_type = FUNCTION_TO_CATEGORY_MAP["плавати"].get(sub_choice, "water")

                add("motor", 1, domains=["water", "universal"])
                add(water_type, 1, domains=["water"])

                # базовий корпус човна: більше пластин + трохи "бортиків"
                hull_plate_qty = max(2, round(2 * body_mult))
                hull_brick_qty = max(1, round(1 * body_mult))

                add("structure:body_plate", hull_plate_qty, domains=["water", "universal"])
                add("structure:body_brick", hull_brick_qty, domains=["water", "universal"])

                add("structure:beam", max(2, round(2 * struct_mult)), domains=["water", "universal"])
                add("structure:axle", max(1, round(1 * struct_mult)), domains=["water", "universal"])
                add("structure:pin", max(2, round(4 * struct_mult)), domains=["water", "universal"])

        # ---- Сенсори ---- #
        if request.sensors:
            add("sensor", len(request.sensors), domains=["universal"])

        return bp

    # ---------------- MAIN ---------------- #

    def configure(self, request: ConfigRequest) -> Dict[str, Any]:
        if not request.functions or request.budget is None or request.weight is None:
            return {"error": "Будь ласка, заповніть усі параметри."}

        try:
            blueprint = self._build_blueprint(request)
        except Exception as e:
            return {"error": f"Помилка при плануванні: {e}"}

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

                # сенсори обираємо по назві
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
                            raise Exception(f"Не знайдено компонент (сенсор): {sensor_name}")
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
                    raise Exception(f"Немає в наявності: {key}")

                for _ in range(quantity):
                    chosen_components.append(component)
                    current_cost += component.get("price") or 0
                    current_weight += component.get("weight") or 0

        except Exception as e:
            return {"error": str(e)}

        # ---- пост-обробка: прибрати недоречні домени ---- #

        def is_forbidden(c: Dict) -> bool:
            cat = (c.get("category") or "").lower()
            dom = (c.get("domain") or "universal").lower()
            if not has_fly and (cat in ("propeller", "wing") or dom == "air"):
                return True
            if not has_swim and (cat == "water" or dom == "water"):
                return True
            return False

        filtered_components = [c for c in chosen_components if not is_forbidden(c)]

        # ---- гарантія: машини мають і колеса, і шини ---- #
        wheel_count = sum(1 for c in filtered_components if c.get("category") == "wheel")
        tire_count = sum(1 for c in filtered_components if c.get("category") == "tire")

        # якщо є колеса, але немає шин – додаємо шини
        if wheel_count > 0 and tire_count == 0:
            tire_comp = self._find_best_component(
                category="tire",
                priority=priority,
                allowed_domains=["ground", "universal"],
            )
            if tire_comp:
                for _ in range(wheel_count):
                    filtered_components.append(tire_comp)

        # якщо є шини, але немає коліс – додаємо диски
        wheel_count = sum(1 for c in filtered_components if c.get("category") == "wheel")
        tire_count = sum(1 for c in filtered_components if c.get("category") == "tire")
        if tire_count > 0 and wheel_count == 0:
            wheel_comp = self._find_best_component(
                category="wheel",
                priority=priority,
                allowed_domains=["ground", "universal"],
            )
            if wheel_comp:
                for _ in range(tire_count):
                    filtered_components.append(wheel_comp)

        # ---- перерахунок ваги/ціни ---- #
        current_cost = sum((c.get("price") or 0) for c in filtered_components)
        current_weight = sum((c.get("weight") or 0) for c in filtered_components)

        if current_cost > request.budget:
            return {
                "error": (
                    f"Конфігурація неможлива. Бюджет перевищено: "
                    f"{current_cost:.2f} > {request.budget:.2f} грн."
                )
            }

        if current_weight > request.weight:
            return {
                "error": (
                    f"Конфігурація неможлива. Вагу перевищено: "
                    f"{current_weight:.2f} > {request.weight:.2f} г."
                )
            }

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
        }
