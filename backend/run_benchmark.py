"""
Standalone Benchmark Script — запускає ExperimentRunner без залежності від БД.

Monkey-patches Repo для читання з JSON, потім запускає повне порівняння
Greedy vs Genetic Algorithm для серії N.

Usage:
    python run_benchmark.py
"""

import sys
import os
import json
import time
import copy
import random
import math
import statistics
from pathlib import Path

# Додаємо backend до PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────
#  1) Завантаження компонентів з JSON
# ─────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "app" / "data" / "lego_components.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    ALL_COMPONENTS = json.load(f)

print(f"[OK] Loaded {len(ALL_COMPONENTS)} components from JSON")

# ─────────────────────────────────────────────────
#  2) Monkey-patch Repo щоб не потрібна БД
# ─────────────────────────────────────────────────
from unittest.mock import MagicMock

# Мокаємо database модуль щоб уникнути підключення до БД
import app.db.database as db_module
db_module.get_engine = MagicMock()
db_module.get_session_factory = MagicMock()

from app.db.repo import Repo

# Патчимо Repo
_original_init = Repo.__init__

def _patched_init(self, db=None):
    self._db = None
    self._owns_session = False

Repo.__init__ = _patched_init
Repo.get_all_components = lambda self: copy.deepcopy(ALL_COMPONENTS)

# ─────────────────────────────────────────────────
#  3) Імпортуємо алгоритми і тулзи
# ─────────────────────────────────────────────────
from app.services.greedy import GreedyConfigurator
from app.services.genetic import GeneticAlgorithmOptimizer
from app.models.dto import ConfigRequest

# ─────────────────────────────────────────────────
#  4) Синтетичний генератор (з analytics.py)
# ─────────────────────────────────────────────────
def generate_synthetic_dataset(real_components, target_n):
    if not real_components:
        return []
    result = copy.deepcopy(real_components[:target_n])
    if len(result) >= target_n:
        return result[:target_n]
    current_id = max(c["id"] for c in real_components) + 1
    while len(result) < target_n:
        donor = random.choice(real_components)
        clone = copy.deepcopy(donor)
        clone["id"] = current_id
        clone["name"] = f"{donor['name']} (Syn-{current_id})"
        clone["price"] = max(1, round(clone["price"] * random.uniform(0.8, 1.2)))
        clone["weight"] = max(0.1, round(clone["weight"] * random.uniform(0.9, 1.1), 2))
        elec = clone.get("electronics") or {}
        if elec.get("rpm_nominal") is not None:
            elec["rpm_nominal"] = max(1, int(elec["rpm_nominal"] * random.uniform(0.85, 1.15)))
        if elec.get("torque_nominal_ncm") is not None:
            elec["torque_nominal_ncm"] = max(0.1, round(elec["torque_nominal_ncm"] * random.uniform(0.9, 1.1), 1))
        result.append(clone)
        current_id += 1
    return result

# ─────────────────────────────────────────────────
#  5) Тестовий запит
# ─────────────────────────────────────────────────
def make_test_request(eco_mode=False):
    return ConfigRequest(
        functions=["Їздити"],
        subFunctions={"Їздити": "колеса"},
        budget=50000,
        weight=20000,
        priority="balanced",
        sensors=["Ultrasonic"],
        complexityLevel=3,
        terrain="indoor",
        sizeClass="medium",
        eco_mode=eco_mode,
    )

# ─────────────────────────────────────────────────
#  6) Benchmark runner
# ─────────────────────────────────────────────────
def time_greedy(dataset, request):
    configurator = GreedyConfigurator(dataset)
    t0 = time.perf_counter()
    result = configurator.configure(request)
    elapsed = time.perf_counter() - t0
    return {
        "time_ms": elapsed * 1000,
        "success": "error" not in result,
        "parts_count": len(result.get("selected", [])),
        "total_price": result.get("total_price", 0),
    }

def time_genetic(dataset, request, population_size=30, generations=20):
    optimizer = GeneticAlgorithmOptimizer(
        dataset,
        population_size=population_size,
        generations=generations,
        mutation_rate=0.1,
        crossover_rate=0.7,
        tournament_size=3,
        elitism_pct=0.1,
    )
    t0 = time.perf_counter()
    result = optimizer.optimize(request)
    elapsed = time.perf_counter() - t0
    return {
        "time_ms": elapsed * 1000,
        "success": "error" not in result,
        "parts_count": len(result.get("selected", [])),
        "fitness": result.get("ga_stats", {}).get("final_fitness", 0),
    }


def run_full_benchmark():
    print("\n" + "=" * 70)
    print("  LEGO Configurator - Performance Benchmark")
    print("=" * 70)

    N_VALUES = [100, 200, 500, 1000, 2000, 5000, 10000]
    RUNS = 3  # прогонів для усереднення
    GA_POP = 30
    GA_GEN = 20

    request = make_test_request()

    results = []

    for n in N_VALUES:
        print(f"\n{'-' * 50}")
        print(f"  N = {n}")
        print(f"{'-' * 50}")

        # Генерація датасету
        t_gen_start = time.perf_counter()
        dataset = generate_synthetic_dataset(ALL_COMPONENTS, n)
        t_gen = (time.perf_counter() - t_gen_start) * 1000
        print(f"  Dataset ({len(dataset)} items) generated in {t_gen:.1f} ms")

        # --- GREEDY ---
        greedy_times = []
        greedy_success = 0
        for r in range(RUNS):
            res = time_greedy(dataset, request)
            greedy_times.append(res["time_ms"])
            if res["success"]:
                greedy_success += 1

        greedy_avg = statistics.mean(greedy_times)
        greedy_min = min(greedy_times)
        greedy_max = max(greedy_times)
        greedy_std = statistics.stdev(greedy_times) if len(greedy_times) > 1 else 0

        print(f"  Greedy:  avg={greedy_avg:.2f} ms  min={greedy_min:.2f}  max={greedy_max:.2f}  std={greedy_std:.2f}  success={greedy_success}/{RUNS}")

        # --- GENETIC (bench params) ---
        ga_times = []
        ga_fitnesses = []
        ga_success = 0
        for r in range(RUNS):
            res = time_genetic(dataset, request, population_size=GA_POP, generations=GA_GEN)
            ga_times.append(res["time_ms"])
            if res["success"]:
                ga_success += 1
                ga_fitnesses.append(res.get("fitness", 0))

        ga_avg = statistics.mean(ga_times)
        ga_min = min(ga_times)
        ga_max = max(ga_times)
        ga_std = statistics.stdev(ga_times) if len(ga_times) > 1 else 0
        ga_fitness_avg = statistics.mean(ga_fitnesses) if ga_fitnesses else 0

        print(f"  GA(p={GA_POP},g={GA_GEN}): avg={ga_avg:.2f} ms  min={ga_min:.2f}  max={ga_max:.2f}  std={ga_std:.2f}  fitness={ga_fitness_avg:.4f}  success={ga_success}/{RUNS}")

        # Теоретична O(N log N)
        n_log_n = n * math.log2(max(n, 2))
        coefficient = greedy_avg / n_log_n * 1000 if n_log_n > 0 else 0

        row = {
            "n": n,
            "greedy_avg_ms": round(greedy_avg, 2),
            "greedy_min_ms": round(greedy_min, 2),
            "greedy_max_ms": round(greedy_max, 2),
            "greedy_std_ms": round(greedy_std, 2),
            "greedy_success": greedy_success,
            "ga_avg_ms": round(ga_avg, 2),
            "ga_min_ms": round(ga_min, 2),
            "ga_max_ms": round(ga_max, 2),
            "ga_std_ms": round(ga_std, 2),
            "ga_fitness": round(ga_fitness_avg, 4),
            "ga_success": ga_success,
            "n_log_n": round(n_log_n, 2),
            "greedy_coefficient": round(coefficient, 6),
            "speed_ratio": round(ga_avg / greedy_avg, 1) if greedy_avg > 0 else 0,
        }
        results.append(row)

    # ─────────────────────────────────────────────────
    #  Додатково: GA з production-параметрами (1 прогін для N=376 реальних)
    # ─────────────────────────────────────────────────
    print(f"\n{'-' * 50}")
    print(f"  GA Production (pop=200, gen=300) - N={len(ALL_COMPONENTS)} (real data)")
    print(f"{'-' * 50}")

    prod_request = make_test_request()
    t0 = time.perf_counter()
    optimizer = GeneticAlgorithmOptimizer(
        ALL_COMPONENTS,
        population_size=200,
        generations=300,
        mutation_rate=0.1,
        crossover_rate=0.7,
        tournament_size=5,
        elitism_pct=0.1,
    )
    prod_result = optimizer.optimize(prod_request)
    prod_elapsed = (time.perf_counter() - t0) * 1000
    prod_fitness = prod_result.get("ga_stats", {}).get("final_fitness", 0)
    prod_parts = len(prod_result.get("selected", []))

    print(f"  Time: {prod_elapsed:.0f} ms ({prod_elapsed/1000:.2f} s)")
    print(f"  Fitness: {prod_fitness:.4f}")
    print(f"  Parts: {prod_parts}")

    # ─────────────────────────────────────────────────
    #  Результати
    # ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SUMMARY TABLE")
    print("=" * 70)
    print(f"\n{'N':>7} | {'Greedy (ms)':>12} | {'GA bench (ms)':>14} | {'GA fitness':>11} | {'Ratio GA/G':>11} | {'N*log2(N)':>12} | {'Coeff':>10}")
    print("-" * 90)
    for r in results:
        print(
            f"{r['n']:>7} | {r['greedy_avg_ms']:>12.2f} | {r['ga_avg_ms']:>14.2f} | {r['ga_fitness']:>11.4f} | {r['speed_ratio']:>10.1f}x | {r['n_log_n']:>12.2f} | {r['greedy_coefficient']:>10.6f}"
        )

    print(f"\n[PROD] GA Production (pop=200, gen=300, N={len(ALL_COMPONENTS)}):")
    print(f"   Time: {prod_elapsed:.0f} ms ({prod_elapsed/1000:.2f} s)")
    print(f"   Fitness: {prod_fitness:.4f}, Parts: {prod_parts}")

    # Перевірка O(N log N)
    coefficients = [r['greedy_coefficient'] for r in results if r['greedy_coefficient'] > 0]
    if coefficients:
        ratio = max(coefficients) / min(coefficients)
        is_nlogn = ratio < 10
        print(f"\n[MATH] Greedy O(N log N) validation:")
        print(f"   Coefficients: {[f'{c:.6f}' for c in coefficients]}")
        print(f"   Range: {ratio:.2f}x  ->  {'CONFIRMED O(N log N)' if is_nlogn else 'DEVIATION from O(N log N)'}")

    # Збереження в JSON
    output = {
        "benchmark_results": results,
        "ga_production": {
            "population_size": 200,
            "generations": 300,
            "n_components": len(ALL_COMPONENTS),
            "time_ms": round(prod_elapsed, 2),
            "time_s": round(prod_elapsed / 1000, 2),
            "fitness": round(prod_fitness, 4),
            "parts_count": prod_parts,
        },
        "complexity_validation": {
            "coefficients": coefficients,
            "coefficient_range": round(ratio, 2) if coefficients else 0,
            "is_approximately_n_log_n": is_nlogn if coefficients else False,
        },
    }

    output_path = Path(__file__).parent / "benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] Results saved to: {output_path}")


if __name__ == "__main__":
    run_full_benchmark()
