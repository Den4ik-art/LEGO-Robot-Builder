"""
Генетичний алгоритм оптимізації конфігурації LEGO-робота.

Реалізує еволюційний підхід до підбору оптимального набору компонентів
з урахуванням обмежень бюджету, маси, структурної цілісності,
симетрії коліс та балансу потужності.
"""

from __future__ import annotations

import random
import math
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable, Set

from app.models.dto import ConfigRequest, PriorityWeights
from app.services.scoring import WeightedScorer
from app.services.sequential import (
    FUNCTION_PERIPHERY_MAP,
    FUNCTION_MOTOR_MAP,
    FUNCTION_DOMAINS,
)
from app.services.constraints import (
    get_complexity_profile,
    is_valid_base,
    get_symmetric_wheel_count,
    check_power_balance,
    prefer_large_motor,
    ComplexityProfile,
    ALLOWED_WHEEL_COUNTS,
    compute_stud_area,
    compute_structural_requirement,
    check_structural_adequacy,
    find_adequate_base,

    check_volume_ratio,
    needs_large_structural,
    has_large_structural,
    find_large_structural,
    compute_connector_deficit,
    find_connector_parts,
    get_function_structural_hint,
    select_decor_parts,
    get_component_volume,
)


# ══════════════════════════════════════════════════════════════════════
#  DOMAIN INFERENCE
# ══════════════════════════════════════════════════════════════════════

CATEGORY_DOMAIN_MAP: Dict[str, str] = {
    "water": "water",
    "propeller": "air",
    "wheel": "ground",
    "tire": "ground",
    "track": "ground",
    "tread": "ground",
}

DOMAIN_NEUTRAL_CATEGORIES: Set[str] = {
    "controller", "power", "sensor",
}


def derive_allowed_domains(functions: List[str]) -> Set[str]:
    """З функцій робота визначає набір допустимих доменів."""
    domains: Set[str] = {"universal"}
    for func in functions:
        func_l = func.lower()
        func_domains = FUNCTION_DOMAINS.get(func_l, ["universal"])
        for d in func_domains:
            domains.add(d)
    return domains


def infer_component_domain(comp: Dict[str, Any]) -> str:
    """Визначає домен компонента з його категорії/даних."""
    domain = comp.get("domain")
    if domain and domain != "universal":
        return domain

    cat = comp.get("category", "")
    if cat in CATEGORY_DOMAIN_MAP:
        return CATEGORY_DOMAIN_MAP[cat]

    name = (comp.get("name") or "").lower()
    if any(kw in name for kw in ["пропелер", "propeller", "крило", "wing"]):
        return "air"
    if any(kw in name for kw in ["корпус судна", "hull", "водомет", "гребн"]):
        return "water"
    if any(kw in name for kw in ["колес", "шин", "гусениц"]):
        return "ground"

    return comp.get("domain", "universal")


# ══════════════════════════════════════════════════════════════════════
#  INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Individual:
    """Одна особина в популяції."""

    chromosome: List[int] = field(default_factory=list)

    # Структуровані блоки
    base_id: Optional[int] = None       # Структурна база
    hub_id: Optional[int] = None
    power_id: Optional[int] = None
    motor_groups: List[Tuple[int, List[int]]] = field(default_factory=list)
    sensor_ids: List[int] = field(default_factory=list)
    structure_ids: List[int] = field(default_factory=list)
    accessory_ids: List[int] = field(default_factory=list)

    # Мета-дані приводу (для Symmetry Rule)
    drive_wheel_id: Optional[int] = None   # ID одного типу колеса
    drive_wheel_count: int = 0              # Кількість коліс (парна)
    drive_tire_id: Optional[int] = None     # ID одного типу шини

    # Оцінки
    fitness: float = 0.0
    total_price: float = 0.0
    total_weight: float = 0.0

    def rebuild_chromosome(self) -> None:
        """Збирає chromosome з структурованих блоків."""
        parts: List[int] = []
        if self.base_id is not None:
            parts.append(self.base_id)
        if self.hub_id is not None:
            parts.append(self.hub_id)
        if self.power_id is not None:
            parts.append(self.power_id)
        for motor_id, periphs in self.motor_groups:
            parts.append(motor_id)
            parts.extend(periphs)
        parts.extend(self.sensor_ids)
        parts.extend(self.structure_ids)
        parts.extend(self.accessory_ids)
        self.chromosome = parts

    def copy(self) -> Individual:
        """Глибока копія."""
        return Individual(
            chromosome=list(self.chromosome),
            base_id=self.base_id,
            hub_id=self.hub_id,
            power_id=self.power_id,
            motor_groups=[(m, list(p)) for m, p in self.motor_groups],
            sensor_ids=list(self.sensor_ids),
            structure_ids=list(self.structure_ids),
            accessory_ids=list(self.accessory_ids),
            drive_wheel_id=self.drive_wheel_id,
            drive_wheel_count=self.drive_wheel_count,
            drive_tire_id=self.drive_tire_id,
            fitness=self.fitness,
            total_price=self.total_price,
            total_weight=self.total_weight,
        )


# ══════════════════════════════════════════════════════════════════════
#  GENETIC ALGORITHM OPTIMIZER
# ══════════════════════════════════════════════════════════════════════

class GeneticAlgorithmOptimizer:
    """
    Генетичний алгоритм оптимізації конфігурації LEGO-робота.

    Ключові особливості:
      - Base-First Rule:       обов'язкова структурна база
      - repair_integrity():    ремонт після crossover/mutation
      - Wheel Symmetry:        один тип коліс, парна кількість
      - Complexity Scaling:     профіль обмежує компоненти
      - Power Balance:          перевірка балансу потужності
    """

    def __init__(
        self,
        components: List[Dict[str, Any]],
        population_size: int = 80,
        generations: int = 150,
        mutation_rate: float = 0.08,
        crossover_rate: float = 0.75,
        tournament_size: int = 5,
        elitism_pct: float = 0.05,
    ):
        self.components = components
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.elitism_count = max(2, int(population_size * elitism_pct))

        self._scorer = WeightedScorer(components)
        self._id_map = self._build_id_map()
        self._cat_index = self._build_category_index()

        self._enriched = False
        self._enrich_domains()

        # Кешуємо base-компоненти
        self._base_candidates: List[Dict] = [
            c for c in self.components if is_valid_base(c)
        ]

    # ──────────────────────────────────────────────────────────────────
    #  ІНДЕКСАЦІЯ
    # ──────────────────────────────────────────────────────────────────

    def _enrich_domains(self) -> None:
        if self._enriched:
            return
        for comp in self.components:
            if not comp.get("domain") or comp["domain"] == "":
                comp["domain"] = infer_component_domain(comp)
        self._enriched = True

    def _build_id_map(self) -> Dict[int, Dict]:
        return {c["id"]: c for c in self.components if "id" in c}

    def _build_category_index(self) -> Dict[str, List[Dict]]:
        idx: Dict[str, List[Dict]] = {}
        for c in self.components:
            cat = c.get("category", "unknown")
            idx.setdefault(cat, []).append(c)
        return idx

    def _get_by_category(self, category: str) -> List[Dict]:
        return self._cat_index.get(category, [])

    def _random_from_category(
        self,
        category: str,
        allowed_domains: Optional[Set[str]] = None,
        max_price: Optional[float] = None,
        max_weight: Optional[float] = None,
        prefer_large: bool = False,
        family_filter: Optional[str] = None,
    ) -> Optional[Dict]:
        """Випадковий компонент з категорії зі строгою доменною фільтрацією."""
        candidates = list(self._get_by_category(category))
        if not candidates:
            return None

        if allowed_domains and category not in DOMAIN_NEUTRAL_CATEGORIES:
            candidates = [
                c for c in candidates
                if (c.get("domain") or infer_component_domain(c)) in allowed_domains
            ]

        if family_filter is not None:
            candidates = [c for c in candidates if c.get("family") == family_filter]

        if max_price is not None:
            candidates = [c for c in candidates if (c.get("price") or 0) <= max_price]
        if max_weight is not None:
            candidates = [c for c in candidates if (c.get("weight") or 0) <= max_weight]

        if not candidates:
            return None

        # Для моторів: перевага великим при prefer_large
        if prefer_large and category == "motor":
            large = [c for c in candidates if prefer_large_motor(c)]
            if large:
                candidates = large

        return random.choice(candidates)

    def _random_base(
        self,
        allowed_domains: Optional[Set[str]] = None,
        max_price: Optional[float] = None,
        max_weight: Optional[float] = None,
    ) -> Optional[Dict]:
        """Випадковий структурний базовий компонент (Base-First)."""
        candidates = list(self._base_candidates)
        if not candidates:
            # Fallback: будь-яка структурна деталь medium+
            candidates = [
                c for c in self._get_by_category("structure")
                if (c.get("geometry") or {}).get("size_class", "medium") != "small"
            ]
        if not candidates:
            return None

        if allowed_domains:
            filtered = [
                c for c in candidates
                if infer_component_domain(c) in allowed_domains
            ]
            if filtered:
                candidates = filtered

        if max_price is not None:
            candidates = [c for c in candidates if (c.get("price") or 0) <= max_price]
        if max_weight is not None:
            candidates = [c for c in candidates if (c.get("weight") or 0) <= max_weight]

        return random.choice(candidates) if candidates else None

    # ──────────────────────────────────────────────────────────────────
    #  ІНІЦІАЛІЗАЦІЯ ПОПУЛЯЦІЇ
    # ──────────────────────────────────────────────────────────────────

    def _generate_random_individual(
        self, request: ConfigRequest, allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> Individual:
        """
        Генерує структурно валідну особину з урахуванням ComplexityProfile.
        """
        budget = float(request.budget)
        mass = float(request.weight)
        ind = Individual()

        has_swim = any("плавати" in f.lower() for f in request.functions)
        has_fly = any("літати" in f.lower() for f in request.functions)

        # ── STEP 0: Base (Base-First Rule) ──
        # Для водних роботів — корпус човна з water категорії
        base = None
        if has_swim:
            water_comps = self._get_by_category("water")
            hull_candidates = [
                c for c in water_comps
                if "корпус" in (c.get("name") or "").lower()
                and (c.get("price") or 0) <= budget * 0.2
                and (c.get("weight") or 0) <= mass * 0.2
            ]
            if not hull_candidates:
                hull_candidates = [
                    c for c in water_comps
                    if (c.get("price") or 0) <= budget * 0.25
                    and (c.get("weight") or 0) <= mass * 0.25
                ]
            if hull_candidates:
                base = random.choice(hull_candidates)

        if not base:
            base = self._random_base(
                allowed_domains=allowed_domains,
                max_price=budget * 0.15,
                max_weight=mass * 0.15,
            )
        if not base:
            base = self._random_base(max_price=budget * 0.3)
        if base:
            ind.base_id = base["id"]
            budget -= base.get("price") or 0
            mass -= base.get("weight") or 0

        # ── STEP 1: Hub ──
        hub = self._random_from_category(
            "controller", allowed_domains=allowed_domains,
            max_price=budget * 0.4, max_weight=mass * 0.4,
        )
        if not hub:
            hub = self._random_from_category("controller", max_price=budget * 0.6)
        if not hub:
            hub = self._random_from_category("controller")
        if not hub:
            return ind

        ind.hub_id = hub["id"]
        budget -= hub.get("price") or 0
        mass -= hub.get("weight") or 0
        max_ports = (hub.get("electronics") or {}).get("ports_count", 4)

        # ── STEP 2: Power ──
        power = self._random_from_category(
            "power", allowed_domains=allowed_domains,
            max_price=budget * 0.25, max_weight=mass * 0.25,
        )
        if not power:
            power = self._random_from_category("power", max_price=budget * 0.5)
        if power:
            ind.power_id = power["id"]
            budget -= power.get("price") or 0
            mass -= power.get("weight") or 0

        # ── STEP 3: Motors + Periphery (по функціях, з Symmetry) ──
        ports_used = 0
        has_drive = any("їздити" in f.lower() for f in request.functions)

        for func in request.functions:
            func_l = func.lower()
            sub_choice = (request.subFunctions or {}).get(func, "").lower()

            motors_needed = 0
            periphery_per_motor = 0
            periphery_cat = None

            if func_l in FUNCTION_MOTOR_MAP:
                sub_map = FUNCTION_MOTOR_MAP[func_l]
                motors_needed, periphery_per_motor = sub_map.get(
                    sub_choice, list(sub_map.values())[0]
                )

            # Обмежуємо моторами за ComplexityProfile, але НЕ нижче потреби функції
            # (квадрокоптер потребує 4 мотори навіть на complexity 2)
            already_added = len(ind.motor_groups)
            motors_needed = min(motors_needed, max(motors_needed, profile.max_motors) - already_added)
            motors_needed = max(0, motors_needed)

            if func_l in FUNCTION_PERIPHERY_MAP:
                sub_map_p = FUNCTION_PERIPHERY_MAP[func_l]
                periphery_cat = sub_map_p.get(sub_choice, list(sub_map_p.values())[0])

            func_domains = set(FUNCTION_DOMAINS.get(func_l, ["universal"]))
            func_domains.add("universal")

            # Вибираємо ОДИН тип мотора (Quality > Quantity)
            chosen_motor = self._random_from_category(
                "motor", allowed_domains=func_domains,
                max_price=budget * 0.3, max_weight=mass * 0.3,
                prefer_large=profile.prefer_large_motors,
            )
            if not chosen_motor:
                chosen_motor = self._random_from_category(
                    "motor", allowed_domains=func_domains,
                )
            if not chosen_motor:
                continue

            # Для Drive: вибираємо ОДИН тип колеса (Symmetry Rule)
            chosen_wheel = None
            chosen_tire = None
            if periphery_cat and "їздити" in func_l:
                chosen_wheel = self._random_from_category(
                    periphery_cat, allowed_domains=func_domains,
                    max_price=budget * 0.2, max_weight=mass * 0.2,
                )
                if periphery_cat == "wheel" and chosen_wheel:
                    chosen_tire = self._random_from_category(
                        "tire", allowed_domains=func_domains,
                        max_price=budget * 0.15, max_weight=mass * 0.15,
                    )

            for mi in range(motors_needed):
                if ports_used >= max_ports or budget <= 0:
                    break

                budget -= chosen_motor.get("price") or 0
                mass -= chosen_motor.get("weight") or 0
                ports_used += 1

                periph_ids: List[int] = []
                if periphery_cat and periphery_per_motor > 0:
                    if "їздити" in func_l and chosen_wheel:
                        # Symmetry: однаковий тип колеса для всіх
                        for _ in range(periphery_per_motor):
                            periph_ids.append(chosen_wheel["id"])
                            budget -= chosen_wheel.get("price") or 0
                            mass -= chosen_wheel.get("weight") or 0

                            if chosen_tire:
                                periph_ids.append(chosen_tire["id"])
                                budget -= chosen_tire.get("price") or 0
                                mass -= chosen_tire.get("weight") or 0
                    else:
                        for _ in range(periphery_per_motor):
                            periph = self._random_from_category(
                                periphery_cat, allowed_domains=func_domains,
                                max_price=budget * 0.2, max_weight=mass * 0.2,
                            )
                            if periph:
                                periph_ids.append(periph["id"])
                                budget -= periph.get("price") or 0
                                mass -= periph.get("weight") or 0

                ind.motor_groups.append((chosen_motor["id"], periph_ids))

            # Зберігаємо wheel/tire ID для Symmetry в мутації
            if chosen_wheel and "їздити" in func_l:
                total_wheels = sum(
                    sum(1 for pid in periphs if self._id_map.get(pid, {}).get("category") in ("wheel", "track"))
                    for _, periphs in ind.motor_groups
                )
                ind.drive_wheel_id = chosen_wheel["id"]
                ind.drive_wheel_count = get_symmetric_wheel_count(total_wheels)
                if chosen_tire:
                    ind.drive_tire_id = chosen_tire["id"]

            # === Контекстні додаткові компоненти ===

            # Крила для літака
            if "літати" in func_l:
                sub_c = (request.subFunctions or {}).get(func, "").lower()
                if "літак" in sub_c:
                    wing_candidates = [
                        c for c in self._get_by_category("structure")
                        if c.get("family") == "wing_plate"
                        and (c.get("price") or 0) <= budget * 0.15
                        and (c.get("weight") or 0) <= mass * 0.15
                    ]
                    if wing_candidates:
                        # Шукаємо ліве і праве крило
                        left_wings = [c for c in wing_candidates if "ліва" in (c.get("name") or "").lower()]
                        right_wings = [c for c in wing_candidates if "права" in (c.get("name") or "").lower()]
                        wing_left = random.choice(left_wings) if left_wings else random.choice(wing_candidates)
                        wing_right = random.choice(right_wings) if right_wings else random.choice(wing_candidates)
                        size_pref = (request.sizeClass or "medium").lower()
                        pairs = 2 if size_pref == "large" else 1
                        for _ in range(pairs):
                            for w in [wing_left, wing_right]:
                                cost = w.get("price") or 0
                                wt = w.get("weight") or 0
                                if cost <= budget and wt <= mass:
                                    ind.structure_ids.append(w["id"])
                                    budget -= cost
                                    mass -= wt

            # Додатковий водний рушій для плавання
            if "плавати" in func_l:
                water_propulsion = [
                    c for c in self._get_by_category("water")
                    if (c.get("price") or 0) <= budget * 0.15
                    and (c.get("weight") or 0) <= mass * 0.15
                ]
                if water_propulsion:
                    wp = random.choice(water_propulsion)
                    cost = wp.get("price") or 0
                    wt = wp.get("weight") or 0
                    if cost <= budget and wt <= mass:
                        ind.accessory_ids.append(wp["id"])
                        budget -= cost
                        mass -= wt

        # ── STEP 4: Sensors (по ComplexityProfile) ──
        sensor_count = 0
        max_sensors = profile.max_sensors
        if request.sensors:
            for sensor_name in request.sensors:
                if ports_used >= max_ports or budget <= 0 or sensor_count >= max_sensors:
                    break
                sensor = self._random_from_category(
                    "sensor", allowed_domains=allowed_domains,
                    max_price=budget * 0.3, max_weight=mass * 0.3,
                )
                if sensor:
                    ind.sensor_ids.append(sensor["id"])
                    budget -= sensor.get("price") or 0
                    mass -= sensor.get("weight") or 0
                    ports_used += 1
                    sensor_count += 1

        # ── STEP 5: Structure — CHASSIS-FIRST with Scale Awareness ──
        #
        # Замість випадкових маленьких деталей, обираємо структуру
        # що відповідає масштабу функціональних компонентів.
        #
        motor_count = len(ind.motor_groups)
        req = compute_structural_requirement(
            motor_count, 1, len(ind.sensor_ids), request.complexityLevel or 2,
        )
        min_area = req["min_stud_area"]

        # 5a. Обов'язкова база (frame/plate) з достатньою площею
        if budget > 1 and mass > 1:
            base_struct = find_adequate_base(
                self.components, motor_count,
                complexity=request.complexityLevel or 2,
                max_price=budget * 0.3,
                max_weight=mass * 0.3,
            )
            if base_struct:
                cost = base_struct.get("price") or 0
                wt = base_struct.get("weight") or 0
                if cost <= budget and wt <= mass:
                    ind.structure_ids.append(base_struct["id"])
                    budget -= cost
                    mass -= wt

        # 5b. Додаткові структурні деталі до мін. потреби
        current_area = sum(
            compute_stud_area(self._id_map[sid])
            for sid in ind.structure_ids if sid in self._id_map
        )
        num_structure = random.randint(profile.min_structure, profile.max_structure)
        attempts = 0
        while len(ind.structure_ids) < num_structure and budget > 1 and mass > 1:
            attempts += 1
            if attempts > num_structure * 2:
                break
            # Якщо площі не вистачає — шукаємо більші деталі
            prefer_large = current_area < min_area
            if prefer_large:
                struct = self._random_from_category(
                    "structure", allowed_domains=allowed_domains,
                    max_price=min(budget * 0.25, budget),
                    max_weight=min(mass * 0.25, mass),
                    family_filter=random.choice(["plate", "frame", "technic_beam"]),
                )
            else:
                struct = self._random_from_category(
                    "structure", allowed_domains=allowed_domains,
                    max_price=min(budget * 0.15, budget),
                    max_weight=min(mass * 0.15, mass),
                )
            if struct:
                cost = struct.get("price") or 0
                wt = struct.get("weight") or 0
                if cost <= budget and wt <= mass:
                    ind.structure_ids.append(struct["id"])
                    budget -= cost
                    mass -= wt
                    current_area += compute_stud_area(struct)

        # ── STEP 6: Accessories (0-2) ──
        num_acc = random.randint(0, 2)
        for _ in range(num_acc):
            if budget <= 1 or mass <= 1:
                break
            acc = self._random_from_category(
                "accessory", allowed_domains=allowed_domains,
                max_price=budget, max_weight=mass,
            )
            if acc:
                cost = acc.get("price") or 0
                wt = acc.get("weight") or 0
                if cost <= budget and wt <= mass:
                    ind.accessory_ids.append(acc["id"])
                    budget -= cost
                    mass -= wt

        ind.rebuild_chromosome()
        return ind

    def _generate_population(
        self, request: ConfigRequest, allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> List[Individual]:
        """Генерує початкову популяцію."""
        population: List[Individual] = []
        for _ in range(self.population_size):
            ind = self._generate_random_individual(request, allowed_domains, profile)
            population.append(ind)
        return population

    # ──────────────────────────────────────────────────────────────────
    #  FITNESS (з урахуванням структурної цілісності)
    # ──────────────────────────────────────────────────────────────────

    def _evaluate_fitness(
        self,
        individual: Individual,
        weights: Dict[str, float],
        max_budget: float,
        max_mass: float,
        allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> float:
        """
        Обчислює fitness: включає перевірку структурної бази, симетрії коліс та балансу потужності.
        """
        if not individual.chromosome:
            return 0.0

        total_score = 0.0
        total_price = 0.0
        total_weight = 0.0
        has_hub = False
        has_motor = False
        has_power = False
        has_base = False
        wheel_ids: List[int] = []
        domain_violations = 0
        seen_ids: Dict[int, int] = {}
        structure_families: Set[str] = set()
        structure_parts: List[Dict[str, Any]] = []
        motor_count = 0
        sensor_count = 0

        # Розраховуємо мінімально необхідну кількість моторів для функцій
        min_required_motors = 0
        if hasattr(self, "current_request"):
            for func in self.current_request.functions:
                func_l = func.lower()
                sub_choice = (self.current_request.subFunctions or {}).get(func, "").lower()
                if func_l in FUNCTION_MOTOR_MAP:
                    sub_map = FUNCTION_MOTOR_MAP[func_l]
                    m_count, _ = sub_map.get(sub_choice, list(sub_map.values())[0])
                    min_required_motors += m_count

        for part_id in individual.chromosome:
            comp = self._id_map.get(part_id)
            if comp is None:
                continue

            total_score += self._scorer.calculate_component_score(comp, weights)
            total_price += comp.get("price") or 0
            total_weight += comp.get("weight") or 0

            cat = comp.get("category", "")

            if cat == "controller":
                has_hub = True
            elif cat == "motor":
                has_motor = True
                motor_count += 1
            elif cat == "power":
                has_power = True
            elif cat in ("wheel", "track"):
                wheel_ids.append(part_id)
            elif cat == "sensor":
                sensor_count += 1

            if cat == "structure":
                fam = comp.get("family")
                if fam:
                    structure_families.add(fam)
                if is_valid_base(comp):
                    has_base = True
                structure_parts.append(comp)

            # Domain check
            if cat not in DOMAIN_NEUTRAL_CATEGORIES:
                comp_domain = infer_component_domain(comp)
                if comp_domain != "universal" and comp_domain not in allowed_domains:
                    domain_violations += 1

            seen_ids[part_id] = seen_ids.get(part_id, 0) + 1

        individual.total_price = total_price
        individual.total_weight = total_weight

        # ── Penalties ──
        penalty = 1.0

        if not has_hub:
            penalty *= 0.001
        if not has_motor:
            penalty *= 0.01
        if not has_power:
            penalty *= 0.5
        if not has_base:
            penalty *= 0.1  # Штраф за відсутність структурної бази

        # Budget/Mass overflow
        if total_price > max_budget:
            overflow_ratio = total_price / max_budget
            penalty *= max(0.01, 1.0 / (overflow_ratio ** 2))
        if total_weight > max_mass:
            overflow_ratio = total_weight / max_mass
            penalty *= max(0.01, 1.0 / (overflow_ratio ** 2))

        # Domain violations
        if domain_violations > 0:
            penalty *= 0.001 ** domain_violations

        # Excessive duplicates (>4 однакових — підозріло)
        excessive_duplicates = sum(
            max(0, count - 4) for count in seen_ids.values()
        )
        if excessive_duplicates > 0:
            penalty *= 0.95 ** excessive_duplicates

        # === Motor count exceeds profile ===
        # Дозволяємо перевищення профілю, якщо це вимагається функцією (напр. квадрокоптер)
        effective_max_motors = max(profile.max_motors, min_required_motors)
        if motor_count > effective_max_motors:
            penalty *= 0.8 ** (motor_count - effective_max_motors)

        # === Sensor count exceeds profile ===
        if sensor_count > profile.max_sensors:
            penalty *= 0.9 ** (sensor_count - profile.max_sensors)

        # === Power Balance check ===
        if has_hub and has_motor:
            hub_comp = self._id_map.get(individual.hub_id)
            motor_comps = [
                self._id_map[mid]
                for mid, _ in individual.motor_groups
                if mid in self._id_map
            ]
            if hub_comp and motor_comps:
                if not check_power_balance(hub_comp, motor_comps):
                    penalty *= 0.6  # Мотори перевищують потужність хабу

        # ── Structural Adequacy Check ──
        is_adequate, coverage_ratio = check_structural_adequacy(
            structure_parts, motor_count, 1,
            sensor_count, profile.level,
        )
        if not is_adequate:
            # Робот фізично не може бути зібраний — серйозний штраф
            penalty *= max(0.2, coverage_ratio * 0.5)
        else:
            # Не штрафуємо вагу структурних деталей (вони необхідні)
            # Знімаємо частину mass-penalty пропорційно до структурної ваги
            struct_weight = sum(p.get("weight", 0) for p in structure_parts)
            if total_weight > max_mass and struct_weight > 0:
                functional_weight = total_weight - struct_weight * 0.7
                if functional_weight <= max_mass:
                    # Перевага без структурної ваги — послаблюємо penalty
                    penalty *= 1.5  # частковий відкат

        # ── Volume Ratio Check ──
        functional_comps = [
            self._id_map[pid] for pid in individual.chromosome
            if pid in self._id_map
            and self._id_map[pid].get("category") in ("motor", "sensor", "controller", "power")
        ]
        if structure_parts and functional_comps:
            func_hint_ratio = 1.5
            if hasattr(self, "current_request"):
                func_hint = get_function_structural_hint(self.current_request.functions)
                func_hint_ratio = func_hint["volume_ratio"]
            vol_ok, vol_ratio = check_volume_ratio(
                structure_parts, functional_comps, func_hint_ratio
            )
            if not vol_ok:
                # Structural volume insufficient for functional parts
                penalty *= max(0.5, vol_ratio / func_hint_ratio)
            elif vol_ratio >= func_hint_ratio * 1.2:
                pass  # Good coverage, no extra bonus needed

        # ── Connector Fill Check ──
        if motor_count > 0:
            all_parts = [
                self._id_map[pid] for pid in individual.chromosome
                if pid in self._id_map
            ]
            deficit = compute_connector_deficit(all_parts, motor_count)
            total_deficit = sum(deficit.values())
            if total_deficit > 0:
                # Missing connectors → physically un-buildable
                penalty *= max(0.6, 1.0 - total_deficit * 0.05)

        # ── Scaling Rule Check ──
        if needs_large_structural(profile.level, motor_count):
            all_parts = [
                self._id_map[pid] for pid in individual.chromosome
                if pid in self._id_map
            ]
            if not has_large_structural(all_parts):
                penalty *= 0.7  # Complex robot without large structural part

        # ── Bonuses ──
        bonus = 1.0

        # Wheel Symmetry: всі колеса однакові + парна кількість
        if len(wheel_ids) >= 2:
            if len(set(wheel_ids)) == 1:
                bonus += 0.08  # Посилений бонус за ідеальну симетрію
            else:
                penalty *= 0.7  # === Penalty за змішані колеса ===

            if len(wheel_ids) in ALLOWED_WHEEL_COUNTS:
                bonus += 0.05  # Бонус за парну кількість
            else:
                penalty *= 0.85  # Пенальті за непарну

        # Budget efficiency
        if total_price <= max_budget and total_price > max_budget * 0.7:
            bonus += 0.10

        # Structure diversity & adequacy
        if len(structure_families) >= 3:
            bonus += 0.05
        if len(structure_families) >= 5:
            bonus += 0.05
        if is_adequate:
            bonus += 0.15  # === Structural adequacy bonus ===
        if coverage_ratio >= 1.5:
            bonus += 0.05  # Extra bonus for generous structure

        if has_power:
            bonus += 0.05
        if has_base:
            bonus += 0.10  # === Base-First bonus ===

        # ── Structural Diversity Bonus (Diversity Rule) ──
        # Надаємо бонус якщо є суміш основних типів: цеглинки та пластини
        if "brick" in structure_families and "plate" in structure_families:
            bonus += 0.10
        elif ("brick" in structure_families or "plate" in structure_families) and len(structure_parts) > 6:
            # Якщо багато структурних деталей, але всі одного типу — невеликий штраф
            penalty *= 0.95

        fitness = total_score * penalty * bonus
        individual.fitness = fitness
        return fitness

    def _evaluate_population(
        self,
        population: List[Individual],
        weights: Dict[str, float],
        max_budget: float,
        max_mass: float,
        allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> None:
        for ind in population:
            self._evaluate_fitness(ind, weights, max_budget, max_mass, allowed_domains, profile)

    # ──────────────────────────────────────────────────────────────────
    #  SELECTION
    # ──────────────────────────────────────────────────────────────────

    def _tournament_select(self, population: List[Individual]) -> Individual:
        contestants = random.sample(
            population, min(self.tournament_size, len(population))
        )
        return max(contestants, key=lambda ind: ind.fitness)

    # ──────────────────────────────────────────────────────────────────
    #  CROSSOVER
    # ──────────────────────────────────────────────────────────────────

    def _crossover(
        self, parent1: Individual, parent2: Individual
    ) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        child1 = Individual()
        child2 = Individual()

        # Base
        if random.random() < 0.5:
            child1.base_id, child2.base_id = parent1.base_id, parent2.base_id
        else:
            child1.base_id, child2.base_id = parent2.base_id, parent1.base_id

        # Hub
        if random.random() < 0.5:
            child1.hub_id, child2.hub_id = parent1.hub_id, parent2.hub_id
        else:
            child1.hub_id, child2.hub_id = parent2.hub_id, parent1.hub_id

        # Power
        if random.random() < 0.5:
            child1.power_id, child2.power_id = parent1.power_id, parent2.power_id
        else:
            child1.power_id, child2.power_id = parent2.power_id, parent1.power_id

        # Motor groups
        max_groups = max(len(parent1.motor_groups), len(parent2.motor_groups))
        for i in range(max_groups):
            p1_group = parent1.motor_groups[i] if i < len(parent1.motor_groups) else None
            p2_group = parent2.motor_groups[i] if i < len(parent2.motor_groups) else None

            if p1_group and p2_group:
                if random.random() < 0.5:
                    child1.motor_groups.append((p1_group[0], list(p1_group[1])))
                    child2.motor_groups.append((p2_group[0], list(p2_group[1])))
                else:
                    child1.motor_groups.append((p2_group[0], list(p2_group[1])))
                    child2.motor_groups.append((p1_group[0], list(p1_group[1])))
            elif p1_group:
                target = child1 if random.random() < 0.5 else child2
                target.motor_groups.append((p1_group[0], list(p1_group[1])))
            elif p2_group:
                target = child1 if random.random() < 0.5 else child2
                target.motor_groups.append((p2_group[0], list(p2_group[1])))

        # Drive wheel — наслідуємо від батька (Symmetry Rule)
        if random.random() < 0.5:
            child1.drive_wheel_id = parent1.drive_wheel_id
            child1.drive_wheel_count = parent1.drive_wheel_count
            child1.drive_tire_id = parent1.drive_tire_id
            child2.drive_wheel_id = parent2.drive_wheel_id
            child2.drive_wheel_count = parent2.drive_wheel_count
            child2.drive_tire_id = parent2.drive_tire_id
        else:
            child1.drive_wheel_id = parent2.drive_wheel_id
            child1.drive_wheel_count = parent2.drive_wheel_count
            child1.drive_tire_id = parent2.drive_tire_id
            child2.drive_wheel_id = parent1.drive_wheel_id
            child2.drive_wheel_count = parent1.drive_wheel_count
            child2.drive_tire_id = parent1.drive_tire_id

        # Sensors
        all_sensors = list(set(parent1.sensor_ids + parent2.sensor_ids))
        random.shuffle(all_sensors)
        mid = len(all_sensors) // 2
        child1.sensor_ids = all_sensors[:mid]
        child2.sensor_ids = all_sensors[mid:]

        # Structure (cap to avoid bloat from merging both parents)
        max_struct = max(len(parent1.structure_ids), len(parent2.structure_ids))
        all_structure = parent1.structure_ids + parent2.structure_ids
        random.shuffle(all_structure)
        mid_s = len(all_structure) // 2
        child1.structure_ids = all_structure[:min(mid_s, max_struct)]
        child2.structure_ids = all_structure[mid_s:mid_s + max_struct]

        # Accessories
        all_acc = list(set(parent1.accessory_ids + parent2.accessory_ids))
        random.shuffle(all_acc)
        mid_a = len(all_acc) // 2
        child1.accessory_ids = all_acc[:mid_a]
        child2.accessory_ids = all_acc[mid_a:]

        # Repair Hub
        if child1.hub_id is None and child2.hub_id is not None:
            child1.hub_id = child2.hub_id
        elif child2.hub_id is None and child1.hub_id is not None:
            child2.hub_id = child1.hub_id
        elif child1.hub_id is None and child2.hub_id is None:
            child1.hub_id = parent1.hub_id
            child2.hub_id = parent2.hub_id or parent1.hub_id

        child1.rebuild_chromosome()
        child2.rebuild_chromosome()

        return child1, child2

    # ──────────────────────────────────────────────────────────────────
    #  MUTATION (з урахуванням симетрії коліс)
    # ──────────────────────────────────────────────────────────────────

    def _mutate(
        self, individual: Individual, allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> None:
        """Мутація з дотриманням симетрії та ComplexityProfile."""

        # ── Base ──
        if random.random() < self.mutation_rate:
            new_base = self._random_base(allowed_domains=allowed_domains)
            if new_base:
                individual.base_id = new_base["id"]

        # ── Hub ──
        if random.random() < self.mutation_rate and individual.hub_id:
            new_hub = self._random_from_category(
                "controller", allowed_domains=allowed_domains
            )
            if new_hub:
                individual.hub_id = new_hub["id"]

        # ── Power ──
        if random.random() < self.mutation_rate and individual.power_id:
            new_power = self._random_from_category(
                "power", allowed_domains=allowed_domains
            )
            if new_power:
                individual.power_id = new_power["id"]

        # ── Motor Groups (symmetry-aware) ──
        if random.random() < self.mutation_rate and individual.motor_groups:
            # Мутуємо ВСІ мотори на ОДИН новий тип (consistency)
            new_motor = self._random_from_category(
                "motor", allowed_domains=allowed_domains,
                prefer_large=profile.prefer_large_motors,
            )
            if new_motor:
                for i, (_, periphs) in enumerate(individual.motor_groups):
                    individual.motor_groups[i] = (new_motor["id"], periphs)

        # ── Wheel Symmetry Mutation ──
        if random.random() < self.mutation_rate and individual.drive_wheel_id:
            # Якщо мутуємо колесо — мутуємо ВСІ колеса на один тип
            new_wheel = self._random_from_category(
                "wheel", allowed_domains=allowed_domains
            )
            if not new_wheel:
                new_wheel = self._random_from_category(
                    "track", allowed_domains=allowed_domains
                )
            if new_wheel:
                old_wheel_id = individual.drive_wheel_id
                individual.drive_wheel_id = new_wheel["id"]
                # Замінюємо у всіх periph_ids
                for i, (motor_id, periphs) in enumerate(individual.motor_groups):
                    new_periphs = [
                        new_wheel["id"] if pid == old_wheel_id else pid
                        for pid in periphs
                    ]
                    individual.motor_groups[i] = (motor_id, new_periphs)

        # ── Sensors ──
        for i, sensor_id in enumerate(individual.sensor_ids):
            if random.random() < self.mutation_rate:
                new_sensor = self._random_from_category(
                    "sensor", allowed_domains=allowed_domains
                )
                if new_sensor:
                    individual.sensor_ids[i] = new_sensor["id"]

        # ── Structure ──
        for i, struct_id in enumerate(individual.structure_ids):
            if random.random() < self.mutation_rate:
                new_struct = self._random_from_category(
                    "structure", allowed_domains=allowed_domains
                )
                if new_struct:
                    individual.structure_ids[i] = new_struct["id"]

        # ── Add/remove structure ──
        if random.random() < 0.05 and len(individual.structure_ids) < profile.max_structure:
            new_struct = self._random_from_category(
                "structure", allowed_domains=allowed_domains
            )
            if new_struct:
                individual.structure_ids.append(new_struct["id"])

        if random.random() < 0.03 and len(individual.structure_ids) > profile.min_structure:
            idx = random.randint(0, len(individual.structure_ids) - 1)
            individual.structure_ids.pop(idx)

        # ── Domain cleanup ──
        if random.random() < 0.15:
            self._domain_cleanup(individual, allowed_domains)

        individual.rebuild_chromosome()

    def _domain_cleanup(
        self, individual: Individual, allowed_domains: Set[str]
    ) -> None:
        """Видаляє деталі що порушують доменні обмеження."""
        cleaned: List[int] = []
        for struct_id in individual.structure_ids:
            comp = self._id_map.get(struct_id)
            if comp:
                comp_domain = infer_component_domain(comp)
                if comp_domain == "universal" or comp_domain in allowed_domains:
                    cleaned.append(struct_id)
                else:
                    replacement = self._random_from_category(
                        "structure", allowed_domains=allowed_domains
                    )
                    if replacement:
                        cleaned.append(replacement["id"])
            else:
                cleaned.append(struct_id)
        individual.structure_ids = cleaned

        cleaned_acc: List[int] = []
        for acc_id in individual.accessory_ids:
            comp = self._id_map.get(acc_id)
            if comp:
                comp_domain = infer_component_domain(comp)
                if comp_domain == "universal" or comp_domain in allowed_domains:
                    cleaned_acc.append(acc_id)
        individual.accessory_ids = cleaned_acc

    # ──────────────────────────────────────────────────────────────────
    #  repair_integrity()  — КЛЮЧОВА НОВА ФУНКЦІЯ
    # ──────────────────────────────────────────────────────────────────

    def _repair_integrity(
        self, individual: Individual, allowed_domains: Set[str],
        profile: ComplexityProfile,
    ) -> None:
        """
        Ремонтна функція: гарантує структурну цілісність після crossover/mutation.

        Перевірки:
          1. Base-First:      якщо немає бази — додаємо
          2. Hub:             якщо немає хабу — додаємо
          3. Motor Symmetry:  всі мотори одного типу (per function)
          4. Wheel Symmetry:  всі колеса одного типу, парна кількість
          5. Motor count:     обмежуємо за ComplexityProfile
          6. Sensor count:    обмежуємо за ComplexityProfile
          7. Power Balance:   перевірка живлення
        """

        # Helper: обчислити поточну вартість/вагу
        def _current_cost() -> float:
            total = 0.0
            for pid in individual.chromosome:
                c = self._id_map.get(pid)
                if c:
                    total += c.get("price") or 0
            return total

        def _can_afford(comp: Dict) -> bool:
            """Lightweight check that adding comp won't obviously bloat."""
            return comp is not None

        # 1. Base-First (Scale-Aware: swap small base for adequate one)
        motor_count = len(individual.motor_groups)
        if individual.base_id is None:
            base = find_adequate_base(
                self.components, motor_count,
                complexity=profile.level,
            )
            if not base:
                base = self._random_base(allowed_domains=allowed_domains)
            if base:
                individual.base_id = base["id"]
        else:
            # Перевірка: чи поточна база достатня за площею?
            base_comp = self._id_map.get(individual.base_id)
            if base_comp:
                base_area = compute_stud_area(base_comp)
                req = compute_structural_requirement(motor_count, 1, 0, profile.level)
                if base_area < req["min_stud_area"] * 0.6:
                    # База занадто мала — шукаємо більшу
                    bigger_base = find_adequate_base(
                        self.components, motor_count,
                        complexity=profile.level,
                    )
                    if bigger_base and compute_stud_area(bigger_base) > base_area:
                        individual.base_id = bigger_base["id"]

        # 2. Hub
        if individual.hub_id is None:
            hub = self._random_from_category("controller")
            if hub:
                individual.hub_id = hub["id"]

        # 3. Motor count cap
        # Розраховуємо скільки моторів нам ДІЙСНО потрібно для функцій
        min_required_motors = 0
        if hasattr(self, "current_request"):
            for func in self.current_request.functions:
                func_l = func.lower()
                sub_choice = (self.current_request.subFunctions or {}).get(func, "").lower()
                if func_l in FUNCTION_MOTOR_MAP:
                    sub_map = FUNCTION_MOTOR_MAP[func_l]
                    m_count, _ = sub_map.get(sub_choice, list(sub_map.values())[0])
                    min_required_motors += m_count

        effective_max_motors = max(profile.max_motors, min_required_motors)
        while len(individual.motor_groups) > effective_max_motors:
            individual.motor_groups.pop()

        # 3.5 Context-Specific Repair (Крила, Маніпулятори)
        if hasattr(self, "current_request"):
            for func in self.current_request.functions:
                func_l = func.lower()
                sub_c = (self.current_request.subFunctions or {}).get(func, "").lower()

                # Літак: якщо немає крил — додаємо
                if "літати" in func_l and "літак" in sub_c:
                    has_wings = any(
                        self._id_map.get(sid, {}).get("family") == "wing_plate"
                        for sid in individual.structure_ids
                    )
                    if not has_wings:
                        wing_candidates = [
                            c for c in self._get_by_category("structure")
                            if c.get("family") == "wing_plate"
                        ]
                        if wing_candidates:
                            side_l = [c for c in wing_candidates if "ліва" in (c.get("name") or "").lower()]
                            side_r = [c for c in wing_candidates if "права" in (c.get("name") or "").lower()]
                            w_l = random.choice(side_l) if side_l else wing_candidates[0]
                            w_r = random.choice(side_r) if side_r else wing_candidates[0]
                            individual.structure_ids.extend([w_l["id"], w_r["id"]])

                # Маніпулятор: якщо немає — додаємо
                if "маніпулювати" in func_l:
                    has_manip = any(
                        self._id_map.get(mid, {}).get("category") == "manipulator"
                        for mid, _ in individual.motor_groups
                    ) or any(
                        self._id_map.get(aid, {}).get("category") == "manipulator"
                        for aid in individual.accessory_ids
                    )
                    if not has_manip:
                        manip_comps = self._get_by_category("manipulator")
                        if manip_comps:
                            m_comp = random.choice(manip_comps)
                            # Шукаємо мотор для маніпулятора якщо є порти
                            hub_comp = self._id_map.get(individual.hub_id)
                            max_ports = (hub_comp.get("electronics") or {}).get("ports_count", 4) if hub_comp else 4
                            if len(individual.motor_groups) < max_ports:
                                motor_comps = self._get_by_category("motor")
                                if motor_comps:
                                    ind_motor = random.choice(motor_comps)
                                    individual.motor_groups.append((ind_motor["id"], [m_comp["id"]]))

        # 4. Wheel Symmetry repair
        if individual.drive_wheel_id:
            for i, (motor_id, periphs) in enumerate(individual.motor_groups):
                new_periphs: List[int] = []
                for pid in periphs:
                    comp = self._id_map.get(pid)
                    if comp and comp.get("category") in ("wheel", "track"):
                        # Замінюємо на вибраний тип
                        new_periphs.append(individual.drive_wheel_id)
                    elif comp and comp.get("category") == "tire" and individual.drive_tire_id:
                        new_periphs.append(individual.drive_tire_id)
                    else:
                        new_periphs.append(pid)
                individual.motor_groups[i] = (motor_id, new_periphs)

        # 5. Sensor count cap
        if len(individual.sensor_ids) > profile.max_sensors:
            individual.sensor_ids = individual.sensor_ids[:profile.max_sensors]

        # 6. Structure count & adequacy bounds
        if len(individual.structure_ids) < profile.min_structure:
            deficit = profile.min_structure - len(individual.structure_ids)
            for _ in range(deficit):
                struct = self._random_from_category(
                    "structure", allowed_domains=allowed_domains
                )
                if struct:
                    individual.structure_ids.append(struct["id"])

        if len(individual.structure_ids) > profile.max_structure:
            individual.structure_ids = individual.structure_ids[:profile.max_structure]

        # 7. Structural Adequacy: ensure enough surface area
        struct_parts = [
            self._id_map[sid] for sid in individual.structure_ids
            if sid in self._id_map
        ]
        is_adequate, _ = check_structural_adequacy(
            struct_parts, motor_count, 1, len(individual.sensor_ids),
            profile.level,
        )
        if not is_adequate and len(individual.structure_ids) < profile.max_structure:
            # Додаємо великі пластини/рами до покриття
            for _ in range(3):
                large_struct = self._random_from_category(
                    "structure", allowed_domains=allowed_domains,
                    family_filter=random.choice(["plate", "frame"]),
                )
                if large_struct:
                    individual.structure_ids.append(large_struct["id"])
                    struct_parts.append(large_struct)
                    ok, _ = check_structural_adequacy(
                        struct_parts, motor_count, 1,
                        len(individual.sensor_ids), profile.level,
                    )
                    if ok:
                        break

        # 8. Scaling Rule: complexity > 2 or motors > 2 → need Large structural
        if needs_large_structural(profile.level, motor_count):
            all_parts = [
                self._id_map[pid] for pid in individual.chromosome
                if pid in self._id_map
            ]
            if not has_large_structural(all_parts):
                large = find_large_structural(self.components)
                if large:
                    individual.structure_ids.append(large["id"])

        # 9. Connector Fill: ensure motors have axles + pins
        if motor_count > 0:
            all_chosen = [
                self._id_map[pid] for pid in individual.chromosome
                if pid in self._id_map
            ]
            # Include structure_ids too (they may not be in chromosome yet)
            for sid in individual.structure_ids:
                if sid in self._id_map:
                    all_chosen.append(self._id_map[sid])

            deficit = compute_connector_deficit(all_chosen, motor_count)
            for family, count in deficit.items():
                fill = find_connector_parts(self.components, family, count)
                for fp in fill:
                    individual.structure_ids.append(fp["id"])

        # 10. Volume Ratio: structural volume must cover functional
        if hasattr(self, "current_request"):
            func_hint = get_function_structural_hint(self.current_request.functions)
            target_ratio = func_hint["volume_ratio"]

            struct_comps = [
                self._id_map[sid] for sid in individual.structure_ids
                if sid in self._id_map
            ]
            func_comps = []
            for mid, _ in individual.motor_groups:
                if mid in self._id_map:
                    func_comps.append(self._id_map[mid])
            if individual.hub_id and individual.hub_id in self._id_map:
                func_comps.append(self._id_map[individual.hub_id])
            for sid in individual.sensor_ids:
                if sid in self._id_map:
                    func_comps.append(self._id_map[sid])

            vol_ok, _ = check_volume_ratio(struct_comps, func_comps, target_ratio)
            if not vol_ok and len(individual.structure_ids) < profile.max_structure + 5:
                # Додаємо структурні деталі до покриття ratio
                for _ in range(4):
                    filler = self._random_from_category(
                        "structure", allowed_domains=allowed_domains,
                        family_filter=random.choice(["plate", "brick"]),
                    )
                    if filler:
                        individual.structure_ids.append(filler["id"])
                        struct_comps.append(filler)
                        ok, _ = check_volume_ratio(struct_comps, func_comps, target_ratio)
                        if ok:
                            break

        individual.rebuild_chromosome()

    # ──────────────────────────────────────────────────────────────────
    #  ADAPTIVE MUTATION
    # ──────────────────────────────────────────────────────────────────

    def _adaptive_mutation_rate(
        self, generation: int, stagnation_count: int
    ) -> float:
        base_rate = self.mutation_rate
        if stagnation_count > 10:
            base_rate = min(0.3, base_rate * (1 + stagnation_count * 0.05))
        progress = generation / self.generations
        if progress > 0.8:
            fine_tune_factor = 1.0 - (progress - 0.8) * 2.5
            base_rate *= max(0.5, fine_tune_factor)
        return base_rate

    # ──────────────────────────────────────────────────────────────────
    #  ГОЛОВНИЙ ЕВОЛЮЦІЙНИЙ ЦИКЛ
    # ──────────────────────────────────────────────────────────────────

    def optimize(
        self,
        request: ConfigRequest,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Запускає генетичний алгоритм оптимізації конфігурації."""
        if not request.functions:
            return {"error": "Будь ласка, оберіть хоча б одну функцію."}
        if request.budget is None or request.weight is None:
            return {"error": "Потрібно вказати бюджет та макс. вагу."}

        self.current_request = request

        # ── Complexity Profile ──
        complexity = request.complexityLevel or 2
        profile = get_complexity_profile(complexity)

        # ── Допустимі домени ──
        allowed_domains = derive_allowed_domains(request.functions)

        # ── Ваги (5-Term WSM) ──
        eco_mode = bool(request.eco_mode) if request.eco_mode else False
        if request.weights is not None:
            weights = {
                "speed": request.weights.speed,
                "force": request.weights.force,
                "economy": request.weights.economy,
                "endurance": request.weights.endurance,
                "eco": request.weights.eco,
            }
            if eco_mode:
                from app.services.scoring import WeightedScorer
                weights = WeightedScorer.apply_eco_mode(weights)
        else:
            weights = self._scorer.get_weights_from_priority(request.priority, eco_mode=eco_mode)

        max_budget = float(request.budget)
        max_mass = float(request.weight)

        # ── Масштабуємо population за ComplexityProfile ──
        actual_pop = max(
            50,
            int(self.population_size * profile.ga_population_multiplier)
        )

        start_time = time.time()

        if progress_callback:
            progress_callback(0, self.generations, "Ініціалізація популяції...")

        # ── 1. Ініціалізація ──
        # Тимчасово підміняємо population_size
        original_pop_size = self.population_size
        self.population_size = actual_pop

        population = self._generate_population(request, allowed_domains, profile)

        # repair_integrity для початкової популяції
        for ind in population:
            self._repair_integrity(ind, allowed_domains, profile)

        self._evaluate_population(population, weights, max_budget, max_mass, allowed_domains, profile)

        # Статистика
        best_fitness_history: List[float] = []
        avg_fitness_history: List[float] = []
        std_fitness_history: List[float] = []
        global_best: Optional[Individual] = None
        stagnation_count = 0
        prev_best_fitness = 0.0

        progress_interval = max(1, self.generations // 50)

        # ── 2. Еволюційний цикл (адаптивний часовий бюджет) ──
        time_limit = 52.0  # секунд — лишаємо 3с запасу для фінальної обробки
        max_stagnation = 30  # зупинка при конвергенції
        gen_times: List[float] = []  # час кожного покоління
        generations_completed = 0

        for gen in range(self.generations):
            gen_start = time.time()

            population.sort(key=lambda ind: ind.fitness, reverse=True)

            gen_best = population[0]
            if global_best is None or gen_best.fitness > global_best.fitness:
                global_best = gen_best.copy()

            if abs(gen_best.fitness - prev_best_fitness) < 1e-6:
                stagnation_count += 1
            else:
                stagnation_count = 0
            prev_best_fitness = gen_best.fitness

            fitnesses = [ind.fitness for ind in population]
            best_fitness_history.append(gen_best.fitness)
            avg_fit = sum(fitnesses) / len(fitnesses) if fitnesses else 0
            avg_fitness_history.append(avg_fit)

            if len(fitnesses) > 1:
                variance = sum((f - avg_fit) ** 2 for f in fitnesses) / len(fitnesses)
                std_fitness_history.append(math.sqrt(variance))
            else:
                std_fitness_history.append(0.0)

            if progress_callback and gen % progress_interval == 0:
                phase = "Еволюція" if gen < self.generations * 0.8 else "Фінальна оптимізація"
                progress_callback(
                    gen + 1,
                    self.generations,
                    f"{phase}: покоління {gen+1}/{self.generations} (fitness: {gen_best.fitness:.2f})"
                )

            # ── Early convergence: зупинка при стагнації ──
            if stagnation_count >= max_stagnation:
                generations_completed = gen + 1
                break

            current_mutation_rate = self._adaptive_mutation_rate(gen, stagnation_count)

            # ── Elitism ──
            next_generation: List[Individual] = []
            elite = population[:self.elitism_count]
            for e in elite:
                next_generation.append(e.copy())

            # ── Нащадки ──
            while len(next_generation) < self.population_size:
                parent1 = self._tournament_select(population)
                parent2 = self._tournament_select(population)

                child1, child2 = self._crossover(parent1, parent2)

                old_rate = self.mutation_rate
                self.mutation_rate = current_mutation_rate
                self._mutate(child1, allowed_domains, profile)
                self._mutate(child2, allowed_domains, profile)
                self.mutation_rate = old_rate

                # === repair_integrity після кожного crossover+mutation ===
                self._repair_integrity(child1, allowed_domains, profile)
                self._repair_integrity(child2, allowed_domains, profile)

                next_generation.append(child1)
                if len(next_generation) < self.population_size:
                    next_generation.append(child2)

            self._evaluate_population(
                next_generation, weights, max_budget, max_mass, allowed_domains, profile
            )
            population = next_generation

            # ── Fresh blood при стагнації ──
            if stagnation_count > 20 and stagnation_count % 10 == 0:
                inject_count = max(3, self.population_size // 15)
                population.sort(key=lambda ind: ind.fitness, reverse=True)
                for i in range(inject_count):
                    fresh = self._generate_random_individual(request, allowed_domains, profile)
                    self._repair_integrity(fresh, allowed_domains, profile)
                    self._evaluate_fitness(
                        fresh, weights, max_budget, max_mass, allowed_domains, profile
                    )
                    if len(population) > self.elitism_count + i:
                        population[-(i + 1)] = fresh

            gen_end = time.time()
            gen_times.append(gen_end - gen_start)
            generations_completed = gen + 1

            # ── Адаптивна перевірка часу ──
            elapsed = gen_end - start_time
            avg_gen_time = sum(gen_times[-10:]) / min(len(gen_times), 10)
            if elapsed + avg_gen_time * 1.5 > time_limit:
                break

        # Відновлюємо population_size
        self.population_size = original_pop_size

        # ── 3. Фінальна обробка ──
        if progress_callback:
            progress_callback(
                self.generations, self.generations, "Фінальна обробка результатів..."
            )

        population.sort(key=lambda ind: ind.fitness, reverse=True)
        final_best = population[0]
        if global_best is not None and global_best.fitness > final_best.fitness:
            final_best = global_best

        elapsed = time.time() - start_time

        # Збираємо компоненти
        selected_parts: List[Dict] = []
        warnings: List[str] = []
        domain_issues: List[str] = []

        for part_id in final_best.chromosome:
            comp = self._id_map.get(part_id)
            if comp:
                comp_domain = infer_component_domain(comp)
                cat = comp.get("category", "")
                if (cat not in DOMAIN_NEUTRAL_CATEGORIES
                        and comp_domain != "universal"
                        and comp_domain not in allowed_domains):
                    domain_issues.append(
                        f"{comp.get('name', '?')} (domain={comp_domain}) "
                        f"не відповідає функціям робота"
                    )
                    continue
                selected_parts.append(comp)
            else:
                warnings.append(f"Компонент #{part_id} не знайдено в базі.")

        if domain_issues:
            warnings.append(
                f"Видалено {len(domain_issues)} деталей через невідповідність домену."
            )

        total_price = sum(c.get("price") or 0 for c in selected_parts)
        total_weight = sum(c.get("weight") or 0 for c in selected_parts)

        # ── DECOR PHASE: fill remaining budget with aesthetic parts ──
        remaining_budget_ga = max_budget - total_price
        remaining_mass_ga = max_mass - total_weight
        if remaining_budget_ga > max_budget * 0.10 and remaining_mass_ga > 0:
            decor_parts = select_decor_parts(
                self.components,
                remaining_budget=remaining_budget_ga,
                remaining_mass=remaining_mass_ga,
                target_budget_usage=0.95,
                original_budget=max_budget,
            )
            for dp in decor_parts:
                dp_price = dp.get("price") or 0
                dp_weight = dp.get("weight") or 0
                if (total_price + dp_price) <= max_budget and (total_weight + dp_weight) <= max_mass:
                    selected_parts.append(dp)
                    total_price += dp_price
                    total_weight += dp_weight

        if total_price > max_budget:
            warnings.append(
                f"Ціна ({total_price} грн) перевищує бюджет ({max_budget} грн)."
            )
        if total_weight > max_mass:
            warnings.append(
                f"Вага ({total_weight}г) перевищує максимум ({max_mass}г)."
            )

        result: Dict[str, Any] = {
            "selected": selected_parts,
            "total_price": round(total_price, 2),
            "total_weight": round(total_weight, 1),
            "remaining_budget": round(max_budget - total_price, 2),
            "chromosome": [c.get("id") for c in selected_parts],
            "ga_stats": {
                "generations": self.generations,
                "generations_completed": generations_completed,
                "population_size": actual_pop,
                "complexity_level": profile.level,
                "final_fitness": round(final_best.fitness, 4),
                "best_fitness_history": [
                    round(f, 4) for f in best_fitness_history
                ],
                "avg_fitness_history": [
                    round(f, 4) for f in avg_fitness_history
                ],
                "std_fitness_history": [
                    round(f, 4) for f in std_fitness_history
                ],
                "elapsed_seconds": round(elapsed, 3),
                "total_parts": len(selected_parts),
                "allowed_domains": list(allowed_domains),
                "stagnation_events": stagnation_count,
            },
        }

        if warnings:
            result["warning"] = " | ".join(warnings)

        return result
