"""
Analytics API — Performance Evaluation Endpoints.

POST /analytics/run          — запускає серію експериментів
GET  /analytics/performance  — швидкий тест з дефолтними N
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.analytics import ExperimentRunner

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class ExperimentRequest(BaseModel):
    """Параметри для серії експериментів."""
    n_values: Optional[List[int]] = [100, 500, 1000, 5000, 10000]
    runs_per_n: Optional[int] = 5
    run_ga: Optional[bool] = True
    eco_mode: Optional[bool] = False
    ga_population: Optional[int] = 30
    ga_generations: Optional[int] = 20


@router.post("/run")
def run_experiments(req: ExperimentRequest):
    """
    Запускає повне порівняльне дослідження Greedy vs GA.

    Returns:
        experiments: масив результатів для кожного N
        summary: загальний аналіз (complexity validation, speed ratio)
    """
    runner = ExperimentRunner()
    result = runner.run_full_comparison(
        n_values=req.n_values,
        runs_per_n=req.runs_per_n or 5,
        run_ga=req.run_ga if req.run_ga is not None else True,
        eco_mode=req.eco_mode if req.eco_mode is not None else False,
        ga_population=req.ga_population or 30,
        ga_generations=req.ga_generations or 20,
    )
    return result


@router.get("/performance")
def quick_performance_test(
    n: int = Query(default=1000, ge=100, le=50000, description="Кількість компонентів"),
    runs: int = Query(default=3, ge=1, le=20, description="Кількість повторень"),
    eco_mode: bool = Query(default=False, description="Eco-mode"),
):
    """
    Швидкий тест продуктивності для одного N.

    Returns:
        Результат одного експерименту (Greedy + GA times).
    """
    runner = ExperimentRunner()
    result = runner.run_single_experiment(
        n=n,
        runs=runs,
        run_ga=True,
        eco_mode=eco_mode,
        ga_population=30,
        ga_generations=20,
    )
    return result
