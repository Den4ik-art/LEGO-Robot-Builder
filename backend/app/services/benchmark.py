import time
import random
import copy
from typing import List, Dict
from app.services.greedy import GreedyConfigurator
from app.models.dto import ConfigRequest
from app.db.repo import Repo

class BenchmarkService:
    def __init__(self):
        self.repo = Repo()
        self.real_data = self.repo.get_all_components()

    def _generate_synthetic_data(self, n: int) -> List[Dict]:
        """
        Генерує N компонентів на основі реальних.
        """
        if not self.real_data:
            return []
        
        synthetic = []
        synthetic.extend(copy.deepcopy(self.real_data))
        
        current_id = max(c["id"] for c in self.real_data) + 1
        
        while len(synthetic) < n:
            donor = random.choice(self.real_data)
            new_item = copy.deepcopy(donor)
            new_item["id"] = current_id
            new_item["name"] = f"{donor['name']} (Gen-{current_id})"

            new_item["price"] = round(new_item["price"] * random.uniform(0.8, 1.2))
            new_item["weight"] = round(new_item["weight"] * random.uniform(0.9, 1.1), 2)
            
            if new_item.get("speed"):
                new_item["speed"] = int(new_item["speed"] * random.uniform(0.9, 1.1))
            
            synthetic.append(new_item)
            current_id += 1
            
        return synthetic[:n]

    def run_benchmark(self, n: int):
        """
        Виконує повний цикл тестування.
        """
        # Генерація даних
        start_gen = time.perf_counter()
        dataset = self._generate_synthetic_data(n)
        end_gen = time.perf_counter()
        
        # Ініціалізація алгоритму з новим датасетом
        configurator = GreedyConfigurator(dataset)
        
        # Типовий запит (складний, щоб навантажити алгоритм)
        request = ConfigRequest(
            functions=["їздити", "літати", "сканувати"],
            subFunctions={"їздити": "колеса", "літати": "квадрокоптер"},
            budget=100000,
            weight=50000,
            priority="speed",
            sensors=["Сенсор відстані (УЗ)", "Гіроскоп", "Камера"]
        )
        
        # Виконання алгоритму
        start_algo = time.perf_counter()
        result = configurator.configure(request)
        end_algo = time.perf_counter()
        
        success = "error" not in result
        
        return {
            "n": n,
            "generation_time_ms": (end_gen - start_gen) * 1000,
            "algorithm_time_ms": (end_algo - start_algo) * 1000,
            "total_items_processed": len(dataset),
            "success": success,
            "items_selected": len(result.get("selected", [])) if success else 0
        }