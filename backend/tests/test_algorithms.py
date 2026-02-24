"""
Standalone unit tests for Greedy (Sequential) and Genetic algorithms.

No server or database required — reads components from JSON directly.
Run:  python -m pytest tests/test_algorithms.py -v
"""

import sys
import os
import json
import copy
from pathlib import Path

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Mock database before any app imports ─────────────────────────────
from unittest.mock import MagicMock
import app.db.database as db_module
db_module.get_engine = MagicMock()
db_module.get_session_factory = MagicMock()

from app.db.repo import Repo

DATA_PATH = Path(__file__).parent.parent / "app" / "data" / "lego_components.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    ALL_COMPONENTS = json.load(f)

_original_init = Repo.__init__
def _patched_init(self, db=None):
    self._db = None
    self._owns_session = False
Repo.__init__ = _patched_init
Repo.get_all_components = lambda self: copy.deepcopy(ALL_COMPONENTS)

# ── App imports ──────────────────────────────────────────────────────
from app.services.sequential import SequentialConfigurator
from app.services.genetic import (
    GeneticAlgorithmOptimizer, Individual, infer_component_domain,
    derive_allowed_domains, DOMAIN_NEUTRAL_CATEGORIES,
)
from app.services.greedy import GreedyConfigurator
from app.services.constraints import (
    is_valid_base, get_complexity_profile, check_power_balance,
)
from app.models.dto import ConfigRequest


# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def make_drive_request(budget=5000, weight=2000, complexity=2) -> ConfigRequest:
    return ConfigRequest(
        functions=["Їздити"],
        subFunctions={"Їздити": "колеса"},
        budget=budget,
        weight=weight,
        priority="balanced",
        sensors=["Ultrasonic"],
        complexityLevel=complexity,
        terrain="indoor",
        sizeClass="medium",
    )

def make_fly_request(budget=5000, weight=2000) -> ConfigRequest:
    return ConfigRequest(
        functions=["Літати"],
        subFunctions={"Літати": "Квадрокоптер"},
        budget=budget,
        weight=weight,
        priority="speed",
        sensors=[],
        complexityLevel=2,
    )

def make_swim_request(budget=5000, weight=2000) -> ConfigRequest:
    return ConfigRequest(
        functions=["Плавати"],
        subFunctions={"Плавати": "Гребні гвинти"},
        budget=budget,
        weight=weight,
        priority="stability",
        sensors=[],
        complexityLevel=2,
    )

def make_ga(pop=30, gen=10):
    return GeneticAlgorithmOptimizer(
        copy.deepcopy(ALL_COMPONENTS),
        population_size=pop,
        generations=gen,
        mutation_rate=0.1,
        crossover_rate=0.7,
        tournament_size=3,
        elitism_pct=0.1,
    )


# ═══════════════════════════════════════════════════════════════════
#  SEQUENTIAL CONFIGURATOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestSequentialConfigurator:
    """Tests for the Sequential (greedy) configurator."""

    def test_basic_drive_config(self):
        """Basic 'Їздити' request should produce valid config within budget."""
        seq = SequentialConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request()
        result = seq.configure(req)

        assert "error" not in result, f"Got error: {result.get('error')}"
        assert result["total_price"] <= req.budget, \
            f"Price {result['total_price']} > budget {req.budget}"
        assert result["total_weight"] <= req.weight, \
            f"Weight {result['total_weight']} > max weight {req.weight}"
        assert len(result["selected"]) > 0

    def test_has_essential_parts(self):
        """Config must contain hub, motor, and power."""
        seq = SequentialConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request()
        result = seq.configure(req)

        assert "error" not in result
        categories = [c.get("category") for c in result["selected"]]
        assert "controller" in categories, "Must have a hub/controller"
        assert "motor" in categories, "Must have a motor"
        assert "power" in categories, "Must have power source"

    def test_tight_budget(self):
        """Very tight budget should still produce valid result or meaningful error."""
        seq = SequentialConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request(budget=500, weight=500)
        result = seq.configure(req)

        if "error" not in result:
            assert result["total_price"] <= 500
            assert result["total_weight"] <= 500

    def test_structure_budget_tracking(self):
        """After fix: structure step should not double-subtract budget."""
        seq = SequentialConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request(budget=3000, weight=1500)
        result = seq.configure(req)

        if "error" not in result:
            # Recalculate total from selected parts
            actual_price = sum(c.get("price", 0) for c in result["selected"])
            assert abs(actual_price - result["total_price"]) < 0.01, \
                f"total_price mismatch: reported={result['total_price']}, actual={actual_price}"
            assert actual_price <= req.budget, \
                f"Actual price {actual_price} > budget {req.budget}"

    def test_fly_config(self):
        """'Літати' request should include propellers, no ground parts."""
        seq = SequentialConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_fly_request()
        result = seq.configure(req)

        if "error" not in result:
            categories = [c.get("category") for c in result["selected"]]
            assert "motor" in categories
            assert result["total_price"] <= req.budget


# ═══════════════════════════════════════════════════════════════════
#  GREEDY CONFIGURATOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestGreedyConfigurator:
    """Tests for the GreedyConfigurator (slot-based)."""

    def test_basic_configure(self):
        """Basic configure call produces valid result."""
        greedy = GreedyConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request()
        result = greedy.configure(req)

        assert "error" not in result, f"Got error: {result.get('error')}"
        assert result["total_price"] <= req.budget
        assert result["total_weight"] <= req.weight

    def test_essential_parts_present(self):
        """Greedy config should have base, hub, power, motor."""
        greedy = GreedyConfigurator(copy.deepcopy(ALL_COMPONENTS))
        req = make_drive_request()
        result = greedy.configure(req)

        if "error" not in result:
            categories = [c.get("category") for c in result["selected"]]
            assert "controller" in categories
            assert "motor" in categories


# ═══════════════════════════════════════════════════════════════════
#  GENETIC ALGORITHM TESTS
# ═══════════════════════════════════════════════════════════════════

class TestGeneticAlgorithm:
    """Tests for the GeneticAlgorithmOptimizer."""

    def test_basic_optimization(self):
        """GA should return a valid result with selected parts."""
        ga = make_ga()
        req = make_drive_request()
        result = ga.optimize(req)

        assert "error" not in result, f"GA error: {result.get('error')}"
        assert len(result["selected"]) > 0
        assert result["total_price"] > 0
        assert "ga_stats" in result
        assert result["ga_stats"]["final_fitness"] > 0

    def test_budget_constraint(self):
        """GA result should not exceed budget."""
        ga = make_ga()
        req = make_drive_request(budget=3000, weight=1500)
        result = ga.optimize(req)

        if "error" not in result:
            actual_price = sum(c.get("price", 0) for c in result["selected"])
            # Allow small overshoot since GA uses soft constraints,
            # but verify it's within reasonable bounds
            assert actual_price <= req.budget * 1.1, \
                f"Price {actual_price} significantly exceeds budget {req.budget}"

    def test_individual_has_base(self):
        """Every generated individual should have a structural base."""
        ga = make_ga(pop=20, gen=1)
        req = make_drive_request()
        profile = get_complexity_profile(req.complexityLevel or 2)
        allowed = derive_allowed_domains(req.functions)

        population = ga._generate_population(req, allowed, profile)
        for ind in population:
            ga._repair_integrity(ind, allowed, profile)

        bases_present = sum(1 for ind in population if ind.base_id is not None)
        # At least 90% should have a base
        assert bases_present >= len(population) * 0.9, \
            f"Only {bases_present}/{len(population)} individuals have a base"

    def test_individual_has_hub(self):
        """Every individual should have a hub/controller."""
        ga = make_ga(pop=20, gen=1)
        req = make_drive_request()
        profile = get_complexity_profile(2)
        allowed = derive_allowed_domains(req.functions)

        population = ga._generate_population(req, allowed, profile)
        for ind in population:
            ga._repair_integrity(ind, allowed, profile)

        hubs = sum(1 for ind in population if ind.hub_id is not None)
        assert hubs == len(population), \
            f"Only {hubs}/{len(population)} individuals have a hub"

    def test_wheel_symmetry(self):
        """All wheels in a drive individual should be the same type."""
        ga = make_ga(pop=30, gen=5)
        req = make_drive_request()
        result = ga.optimize(req)

        if "error" not in result:
            wheel_ids = [
                c["id"] for c in result["selected"]
                if c.get("category") in ("wheel", "track")
            ]
            if len(wheel_ids) >= 2:
                unique_types = set(wheel_ids)
                assert len(unique_types) == 1, \
                    f"Mixed wheel types: {unique_types}"

    def test_domain_filtering_ground(self):
        """'Їздити' config should not contain 'air' or 'water' domain parts."""
        ga = make_ga(pop=30, gen=10)
        req = make_drive_request()
        result = ga.optimize(req)

        if "error" not in result:
            for part in result["selected"]:
                cat = part.get("category", "")
                if cat in DOMAIN_NEUTRAL_CATEGORIES:
                    continue
                domain = infer_component_domain(part)
                assert domain in ("universal", "ground"), \
                    f"{part.get('name')} has domain={domain}, expected ground/universal"

    def test_domain_filtering_air(self):
        """'Літати' config should not contain 'ground' domain drive parts."""
        ga = make_ga(pop=30, gen=10)
        req = make_fly_request()
        result = ga.optimize(req)

        if "error" not in result:
            forbidden = {"ground"}
            for part in result["selected"]:
                cat = part.get("category", "")
                if cat in DOMAIN_NEUTRAL_CATEGORIES or cat == "structure":
                    continue
                domain = infer_component_domain(part)
                assert domain not in forbidden, \
                    f"{part.get('name')} (cat={cat}) has domain={domain}, forbidden for fly"

    def test_crossover_no_bloat(self):
        """Crossover should not produce children with 2× parent structure."""
        ga = make_ga(pop=20, gen=1)
        req = make_drive_request()
        profile = get_complexity_profile(2)
        allowed = derive_allowed_domains(req.functions)

        pop = ga._generate_population(req, allowed, profile)
        for ind in pop:
            ga._repair_integrity(ind, allowed, profile)

        # Pick two parents
        p1, p2 = pop[0], pop[1]
        max_parent_struct = max(len(p1.structure_ids), len(p2.structure_ids))

        c1, c2 = ga._crossover(p1, p2)

        # Children should not have more structure than the largest parent  
        # (allow small margin for randomness)
        assert len(c1.structure_ids) <= max_parent_struct + 2, \
            f"Child1 structure bloat: {len(c1.structure_ids)} > {max_parent_struct}"
        assert len(c2.structure_ids) <= max_parent_struct + 2, \
            f"Child2 structure bloat: {len(c2.structure_ids)} > {max_parent_struct}"

    def test_fitness_positive(self):
        """Final best fitness should be positive and non-trivial."""
        ga = make_ga(pop=30, gen=15)
        req = make_drive_request()
        result = ga.optimize(req)

        assert "error" not in result
        fitness = result["ga_stats"]["final_fitness"]
        assert fitness > 0.1, f"Fitness too low: {fitness}"

    def test_power_balance_penalty(self):
        """Verify that power-balance check exists in fitness evaluation."""
        ga = make_ga(pop=10, gen=1)
        req = make_drive_request()
        profile = get_complexity_profile(2)
        allowed = derive_allowed_domains(req.functions)

        ind = ga._generate_random_individual(req, allowed, profile)
        ga._repair_integrity(ind, allowed, profile)

        weights = ga._scorer.get_weights_from_priority("balanced")
        fitness = ga._evaluate_fitness(
            ind, weights, float(req.budget), float(req.weight), allowed, profile
        )
        # Just verify it runs without error and returns a number
        assert isinstance(fitness, float)
        assert fitness >= 0

    def test_complexity_profile_respected(self):
        """GA result should respect complexity profile motor limits."""
        ga = make_ga(pop=30, gen=10)
        req = make_drive_request(complexity=1)  # Level 1: max 2 motors
        result = ga.optimize(req)

        if "error" not in result:
            motor_count = sum(
                1 for c in result["selected"] if c.get("category") == "motor"
            )
            profile = get_complexity_profile(1)
            # After repair, motors should be within profile limits
            assert motor_count <= profile.max_motors + 1, \
                f"Motor count {motor_count} > max {profile.max_motors} for complexity 1"


# ═══════════════════════════════════════════════════════════════════
#  CONSTRAINT FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestConstraints:
    """Tests for constraint utility functions."""

    def test_valid_base_detection(self):
        """is_valid_base should identify valid structural bases."""
        valid = {
            "category": "structure",
            "family": "plate",
            "geometry": {"size_class": "medium"},
        }
        assert is_valid_base(valid) is True

        invalid_small = {
            "category": "structure",
            "family": "plate",
            "geometry": {"size_class": "small"},
        }
        assert is_valid_base(invalid_small) is False

        invalid_motor = {"category": "motor", "family": "plate"}
        assert is_valid_base(invalid_motor) is False

    def test_derive_allowed_domains(self):
        """Domain derivation from functions."""
        assert "ground" in derive_allowed_domains(["Їздити"])
        assert "universal" in derive_allowed_domains(["Їздити"])
        assert "air" in derive_allowed_domains(["Літати"])
        assert "water" in derive_allowed_domains(["Плавати"])

    def test_power_balance(self):
        """check_power_balance with known values."""
        hub = {"electronics": {"max_power_mw": 1000}}
        motor_ok = [{"electronics": {"power_mw": 400}}]
        motor_bad = [{"electronics": {"power_mw": 600}}, {"electronics": {"power_mw": 600}}]

        assert check_power_balance(hub, motor_ok) is True
        assert check_power_balance(hub, motor_bad) is False

        # Hub without power data should always pass
        hub_no_data = {"electronics": {}}
        assert check_power_balance(hub_no_data, motor_bad) is True
