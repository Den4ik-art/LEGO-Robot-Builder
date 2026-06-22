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
from app.services.scoring import WeightedScorer


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

    # ══════════════════════════════════════════════════════════════════════
    #  DASHBOARD ANALYSIS (для аналітичного модуля)
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _compute_characteristics(
        selected_parts: List[Dict[str, Any]],
        scorer: WeightedScorer,
    ) -> Dict[str, float]:
        """
        Обчислює агреговані характеристики робота для Radar Chart.

        Повертає 5 метрик (0..100):
          - speed:     на основі rpm моторів
          - force:     на основі torque моторів
          - economy:   інверсна ціна (дешевше = краще)
          - endurance: інверсна вага (легше = краще)
          - eco:       енергоефективність
        """
        if not selected_parts:
            return {"speed": 0, "force": 0, "economy": 0, "endurance": 0, "eco": 0}

        total_price = sum(c.get("price") or 0 for c in selected_parts)
        total_weight = sum(c.get("weight") or 0 for c in selected_parts)

        # --- Speed (RPM від моторів) ---
        rpms = []
        torques = []
        energies = []
        for comp in selected_parts:
            elec = comp.get("electronics") or {}
            rpm = elec.get("rpm_nominal")
            if rpm is not None:
                rpms.append(float(rpm))
            torque = elec.get("torque_nominal_ncm")
            if torque is not None:
                torques.append(float(torque))
            voltage = elec.get("voltage_v")
            current = elec.get("max_current_a")
            if voltage is not None and current is not None:
                energies.append(float(voltage) * float(current))

        # Нормалізація до 0..100
        # Speed: середній RPM як частка від максимально можливого (~185 RPM для Technic XL)
        speed_score = 0.0
        if rpms:
            avg_rpm = statistics.mean(rpms)
            speed_score = min(100, (avg_rpm / 200) * 100)

        # Force: середній torque як частка від макс. (~25 N·cm)
        force_score = 0.0
        if torques:
            avg_torque = statistics.mean(torques)
            force_score = min(100, (avg_torque / 30) * 100)

        # Economy: інверсна ціна (менше = краще), 50000 грн — макс. бюджет
        economy_score = max(0, min(100, (1 - total_price / 50000) * 100))

        # Endurance: інверсна вага (менше = краще), 20000 г — макс. вага
        endurance_score = max(0, min(100, (1 - total_weight / 20000) * 100))

        # Eco: інверсне енергоспоживання
        eco_score = 50.0  # default
        if energies:
            avg_energy = statistics.mean(energies)
            eco_score = max(0, min(100, (1 - avg_energy / 10) * 100))

        return {
            "speed": round(speed_score, 1),
            "force": round(force_score, 1),
            "economy": round(economy_score, 1),
            "endurance": round(endurance_score, 1),
            "eco": round(eco_score, 1),
        }

    def run_dashboard_analysis(
        self,
        n: int = 1000,
        run_greedy: bool = True,
        run_genetic: bool = True,
        eco_mode: bool = False,
        ga_population: int = 50,
        ga_generations: int = 30,
    ) -> Dict[str, Any]:
        """
        Запускає аналіз для Dashboard (фронтенд аналітичний модуль).

        Повертає структуровані дані для BarChart, RadarChart, та LineChart:
        {
          "n": 1000,
          "algorithms": {
            "Greedy": { "time_ms", "fitness", "success", "characteristics": {...} },
            "Genetic": { ..., "convergence": [...] }
          }
        }
        """
        request = make_test_request(eco_mode=eco_mode)
        dataset = generate_synthetic_dataset(self.real_components, n)
        scorer = WeightedScorer(dataset)
        weights = scorer.get_weights_from_priority(request.priority, eco_mode=eco_mode)

        algorithms: Dict[str, Any] = {}

        # ── GREEDY (Жадібний) ──
        if run_greedy:
            configurator = GreedyConfigurator(dataset)

            t0 = time.perf_counter()
            greedy_result = configurator.configure(request)
            greedy_time = (time.perf_counter() - t0) * 1000

            greedy_parts = greedy_result.get("selected", [])
            greedy_success = "error" not in greedy_result

            # Обчислюємо fitness як середню зважену оцінку (0..100)
            greedy_fitness = 0.0
            greedy_cat_scores = {}
            greedy_cat_price = {}
            greedy_cat_weight = {}
            if greedy_parts:
                scores = []
                for comp in greedy_parts:
                    score = scorer.calculate_component_score(comp, weights)
                    scores.append(score)
                    cat = comp.get("category", "unknown")
                    greedy_cat_scores[cat] = greedy_cat_scores.get(cat, 0.0) + score
                    greedy_cat_price[cat] = greedy_cat_price.get(cat, 0.0) + (comp.get("price") or 0)
                    greedy_cat_weight[cat] = greedy_cat_weight.get(cat, 0.0) + (comp.get("weight") or 0)
                
                total_raw = sum(scores)
                greedy_fitness = (total_raw / len(scores)) / 2.5 * 100
                
                if total_raw > 0:
                    for cat in greedy_cat_scores:
                        greedy_cat_scores[cat] = round((greedy_cat_scores[cat] / total_raw) * greedy_fitness, 2)

            characteristics = self._compute_characteristics(greedy_parts, scorer)

            algorithms["Greedy"] = {
                "name": "Greedy",
                "time_ms": round(greedy_time, 2),
                "fitness": round(greedy_fitness, 2),
                "success": greedy_success,
                "parts_count": len(greedy_parts),
                "total_price": greedy_result.get("total_price", 0),
                "total_weight": greedy_result.get("total_weight", 0),
                "characteristics": characteristics,
                "category_breakdown": greedy_cat_scores,
                "category_price": greedy_cat_price,
                "category_weight": greedy_cat_weight,
            }

        # ── GENETIC (Генетичний) ──
        if run_genetic:
            optimizer = GeneticAlgorithmOptimizer(
                dataset,
                population_size=ga_population,
                generations=ga_generations,
                mutation_rate=0.08,
                crossover_rate=0.75,
                tournament_size=5,
                elitism_pct=0.05,
            )

            t0 = time.perf_counter()
            ga_result = optimizer.optimize(request)
            ga_time = (time.perf_counter() - t0) * 1000

            ga_parts = ga_result.get("selected", [])
            ga_success = "error" not in ga_result
            ga_stats = ga_result.get("ga_stats", {})

            # Fitness від GA — нормалізуємо аналогічно до Greedy
            ga_fitness = 0.0
            ga_cat_scores = {}
            ga_cat_price = {}
            ga_cat_weight = {}
            if ga_parts:
                ga_scores = []
                for comp in ga_parts:
                    score = scorer.calculate_component_score(comp, weights)
                    ga_scores.append(score)
                    cat = comp.get("category", "unknown")
                    ga_cat_scores[cat] = ga_cat_scores.get(cat, 0.0) + score
                    ga_cat_price[cat] = ga_cat_price.get(cat, 0.0) + (comp.get("price") or 0)
                    ga_cat_weight[cat] = ga_cat_weight.get(cat, 0.0) + (comp.get("weight") or 0)
                
                total_raw = sum(ga_scores)
                ga_fitness = (total_raw / len(ga_scores)) / 2.5 * 100
                
                if total_raw > 0:
                    for cat in ga_cat_scores:
                        ga_cat_scores[cat] = round((ga_cat_scores[cat] / total_raw) * ga_fitness, 2)

            # Convergence history (повна, не обрізана)
            best_hist = ga_stats.get("best_fitness_history", [])
            avg_hist = ga_stats.get("avg_fitness_history", [])
            std_hist = ga_stats.get("std_fitness_history", [])
            convergence = []
            for i in range(len(best_hist)):
                convergence.append({
                    "generation": i + 1,
                    "best_fitness": round(best_hist[i], 4) if i < len(best_hist) else 0,
                    "avg_fitness": round(avg_hist[i], 4) if i < len(avg_hist) else 0,
                    "std_fitness": round(std_hist[i], 4) if i < len(std_hist) else 0,
                })

            characteristics = self._compute_characteristics(ga_parts, scorer)

            algorithms["Genetic"] = {
                "name": "Genetic",
                "time_ms": round(ga_time, 2),
                "fitness": round(ga_fitness, 2),
                "success": ga_success,
                "parts_count": len(ga_parts),
                "total_price": ga_result.get("total_price", 0),
                "total_weight": ga_result.get("total_weight", 0),
                "characteristics": characteristics,
                "category_breakdown": ga_cat_scores,
                "category_price": ga_cat_price,
                "category_weight": ga_cat_weight,
                "convergence": convergence,
                "ga_meta": {
                    "generations_completed": ga_stats.get("generations_completed", 0),
                    "population_size": ga_stats.get("population_size", 0),
                    "stagnation_events": ga_stats.get("stagnation_events", 0),
                    "elapsed_seconds": ga_stats.get("elapsed_seconds", 0),
                },
            }

        return {
            "n": n,
            "algorithms": algorithms,
        }
