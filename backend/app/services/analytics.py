"""
Analytics Module — Performance Evaluation (T(N) vs N).

Модуль для порівняльного аналізу Greedy vs Genetic Algorithm:
  - Запускає обидва алгоритми з синтетичними наборами даних різного розміру N
  - Вимірює час виконання (average over R runs)
  - Повертає дані для графіка T(N) vs N
  - Валідує обмеження O(N log N) для Greedy

Академічний рівень — ФІТ КНУ, 122 КН.
"""

from __future__ import annotations

import copy
import math
import random
import time
import statistics
from typing import List, Dict, Any, Optional, Callable

from app.db.repo import Repo
from app.models.dto import ConfigRequest
from app.services.greedy import GreedyConfigurator
from app.services.genetic import GeneticAlgorithmOptimizer


# ══════════════════════════════════════════════════════════════════════
#  SYNTHETIC DATA GENERATOR
# ══════════════════════════════════════════════════════════════════════

def generate_synthetic_dataset(
    real_components: List[Dict[str, Any]],
    target_n: int,
) -> List[Dict[str, Any]]:
    """
    Генерує N компонентів шляхом клонування реальних з варіаціями.

    Args:
        real_components: Реальна база компонентів (376 шт.)
        target_n: Бажана кількість компонентів.

    Returns:
        Список з target_n компонентів.
    """
    if not real_components:
        return []

    # Починаємо з реальних даних
    result = copy.deepcopy(real_components[:target_n])

    if len(result) >= target_n:
        return result[:target_n]

    current_id = max(c["id"] for c in real_components) + 1

    while len(result) < target_n:
        donor = random.choice(real_components)
        clone = copy.deepcopy(donor)
        clone["id"] = current_id
        clone["name"] = f"{donor['name']} (Syn-{current_id})"

        # Варіація параметрів (±10-20%)
        clone["price"] = max(1, round(clone["price"] * random.uniform(0.8, 1.2)))
        clone["weight"] = max(0.1, round(clone["weight"] * random.uniform(0.9, 1.1), 2))

        elec = clone.get("electronics") or {}
        if elec.get("rpm_nominal") is not None:
            elec["rpm_nominal"] = max(1, int(elec["rpm_nominal"] * random.uniform(0.85, 1.15)))
        if elec.get("torque_nominal_ncm") is not None:
            elec["torque_nominal_ncm"] = max(0.1, round(elec["torque_nominal_ncm"] * random.uniform(0.9, 1.1), 1))
        if elec.get("max_current_a") is not None:
            elec["max_current_a"] = max(0.01, round(elec["max_current_a"] * random.uniform(0.9, 1.1), 3))

        result.append(clone)
        current_id += 1

    return result


# ══════════════════════════════════════════════════════════════════════
#  DEFAULT TEST REQUEST
# ══════════════════════════════════════════════════════════════════════

def make_test_request(eco_mode: bool = False) -> ConfigRequest:
    """Створює типовий тестовий запит для бенчмарків."""
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


# ══════════════════════════════════════════════════════════════════════
#  EXPERIMENT RUNNER
# ══════════════════════════════════════════════════════════════════════

class ExperimentRunner:
    """
    Запускає серію експериментів для скільки-різних N.

    Usage:
        runner = ExperimentRunner()
        results = runner.run_full_comparison(
            n_values=[100, 1000, 10000],
            runs_per_n=10,
        )
    """

    def __init__(self):
        self.repo = Repo()
        self.real_components = self.repo.get_all_components()

    def _time_greedy(
        self,
        dataset: List[Dict[str, Any]],
        request: ConfigRequest,
    ) -> Dict[str, Any]:
        """Вимірює час виконання Greedy."""
        configurator = GreedyConfigurator(dataset)

        t0 = time.perf_counter()
        result = configurator.configure(request)
        elapsed = time.perf_counter() - t0

        return {
            "time_ms": elapsed * 1000,
            "success": "error" not in result,
            "parts_count": len(result.get("selected", [])),
            "total_price": result.get("total_price", 0),
            "total_weight": result.get("total_weight", 0),
        }

    def _time_genetic(
        self,
        dataset: List[Dict[str, Any]],
        request: ConfigRequest,
        population_size: int = 30,
        generations: int = 20,
    ) -> Dict[str, Any]:
        """Вимірює час виконання GA (зі зменшеними параметрами для швидкості)."""
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
            "total_price": result.get("total_price", 0),
            "total_weight": result.get("total_weight", 0),
            "fitness": result.get("ga_stats", {}).get("final_fitness", 0),
        }

    def run_single_experiment(
        self,
        n: int,
        runs: int = 5,
        run_ga: bool = True,
        eco_mode: bool = False,
        ga_population: int = 30,
        ga_generations: int = 20,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Запускає один експеримент для конкретного N.

        Args:
            n:           Кількість компонентів у датасеті.
            runs:        Кількість повторень (для усереднення).
            run_ga:      Чи запускати GA (False = тільки Greedy).
            eco_mode:    Чи тестувати в eco-mode.
            ga_population: Розмір популяції GA.
            ga_generations: Кількість поколінь GA.
            progress_callback: Callback для прогресу.

        Returns:
            Результати експерименту.
        """
        request = make_test_request(eco_mode=eco_mode)

        # Генерація синтетичного датасету
        if progress_callback:
            progress_callback(f"Генерація датасету N={n}...")

        t_gen_start = time.perf_counter()
        dataset = generate_synthetic_dataset(self.real_components, n)
        t_gen = (time.perf_counter() - t_gen_start) * 1000

        # Greedy runs
        greedy_times: List[float] = []
        greedy_success = 0
        for r in range(runs):
            if progress_callback:
                progress_callback(f"Greedy run {r + 1}/{runs} (N={n})...")
            res = self._time_greedy(dataset, request)
            greedy_times.append(res["time_ms"])
            if res["success"]:
                greedy_success += 1

        # GA runs (optional)
        ga_times: List[float] = []
        ga_success = 0
        ga_avg_fitness = 0.0
        if run_ga:
            fitnesses: List[float] = []
            for r in range(runs):
                if progress_callback:
                    progress_callback(f"GA run {r + 1}/{runs} (N={n})...")
                res = self._time_genetic(
                    dataset, request,
                    population_size=ga_population,
                    generations=ga_generations,
                )
                ga_times.append(res["time_ms"])
                if res["success"]:
                    ga_success += 1
                    fitnesses.append(res.get("fitness", 0))
            if fitnesses:
                ga_avg_fitness = statistics.mean(fitnesses)

        # Обчислення статистики
        result: Dict[str, Any] = {
            "n": n,
            "runs": runs,
            "dataset_generation_ms": round(t_gen, 2),
            "greedy": {
                "avg_time_ms": round(statistics.mean(greedy_times), 3),
                "min_time_ms": round(min(greedy_times), 3),
                "max_time_ms": round(max(greedy_times), 3),
                "std_dev_ms": round(statistics.stdev(greedy_times), 3) if len(greedy_times) > 1 else 0.0,
                "success_rate": greedy_success / runs,
            },
        }

        if run_ga:
            result["genetic"] = {
                "avg_time_ms": round(statistics.mean(ga_times), 3),
                "min_time_ms": round(min(ga_times), 3),
                "max_time_ms": round(max(ga_times), 3),
                "std_dev_ms": round(statistics.stdev(ga_times), 3) if len(ga_times) > 1 else 0.0,
                "success_rate": ga_success / runs,
                "avg_fitness": round(ga_avg_fitness, 4),
                "population_size": ga_population,
                "generations": ga_generations,
            }

        # Approximate complexity validation
        if n > 0:
            n_log_n = n * math.log2(max(n, 2))
            result["theoretical_n_log_n"] = round(n_log_n, 2)
            if len(greedy_times) > 0 and greedy_times[0] > 0:
                result["greedy_coefficient"] = round(
                    statistics.mean(greedy_times) / n_log_n * 1000, 6
                )

        return result

    def run_full_comparison(
        self,
        n_values: Optional[List[int]] = None,
        runs_per_n: int = 5,
        run_ga: bool = True,
        eco_mode: bool = False,
        ga_population: int = 30,
        ga_generations: int = 20,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Запускає повне порівняння Greedy vs GA для серії N.

        Args:
            n_values:    Список N для тестування. Default: [100, 500, 1000, 5000, 10000].
            runs_per_n:  Кількість повторень для кожного N.
            run_ga:      Чи запускати GA.
            eco_mode:    Чи тестувати eco-mode.
            ga_population: Розмір популяції GA.
            ga_generations: Кількість поколінь GA.
            progress_callback: Callback для прогресу.

        Returns:
            {
                "experiments": [...],
                "summary": {...},
            }
        """
        if n_values is None:
            n_values = [100, 500, 1000, 5000, 10000]

        experiments: List[Dict[str, Any]] = []
        total_time_start = time.perf_counter()

        for i, n in enumerate(n_values):
            if progress_callback:
                progress_callback(f"Експеримент {i + 1}/{len(n_values)}: N={n}")

            exp = self.run_single_experiment(
                n=n,
                runs=runs_per_n,
                run_ga=run_ga,
                eco_mode=eco_mode,
                ga_population=ga_population,
                ga_generations=ga_generations,
                progress_callback=progress_callback,
            )
            experiments.append(exp)

        total_time = (time.perf_counter() - total_time_start) * 1000

        # Summary
        summary: Dict[str, Any] = {
            "total_experiments": len(experiments),
            "total_time_ms": round(total_time, 2),
            "n_values": n_values,
            "runs_per_n": runs_per_n,
            "eco_mode": eco_mode,
        }

        # Greedy: перевірка O(N log N) — порівнюємо коефіцієнти
        coefficients = [
            exp.get("greedy_coefficient", 0)
            for exp in experiments
            if exp.get("greedy_coefficient", 0) > 0
        ]
        if coefficients:
            summary["greedy_complexity_analysis"] = {
                "coefficients": coefficients,
                "coefficient_range": round(max(coefficients) / max(min(coefficients), 1e-9), 2),
                "is_approximately_n_log_n": (max(coefficients) / max(min(coefficients), 1e-9)) < 10,
            }

        # GA vs Greedy speed ratio
        if run_ga and len(experiments) >= 2:
            speed_ratios: List[float] = []
            for exp in experiments:
                if "genetic" in exp:
                    g_time = exp["greedy"]["avg_time_ms"]
                    ga_time = exp["genetic"]["avg_time_ms"]
                    if g_time > 0:
                        speed_ratios.append(ga_time / g_time)
            if speed_ratios:
                summary["ga_vs_greedy_speed_ratio"] = {
                    "avg_ratio": round(statistics.mean(speed_ratios), 2),
                    "description": f"GA повільніше у {statistics.mean(speed_ratios):.1f}x разів",
                }

        return {
            "experiments": experiments,
            "summary": summary,
        }
