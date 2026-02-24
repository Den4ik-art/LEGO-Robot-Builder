"""
End-to-end тест API конфігурації — точно як фронтенд надсилає запити.
Перевіряє що Greedy і GA повертають коректні конфігурації для кінцевого користувача.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import requests

BASE = "http://127.0.0.1:8000"

# Набір реальних запитів, які користувач може надіслати з UI
USER_SCENARIOS = [
    {
        "name": "Машинка на колесах (Greedy)",
        "endpoint": "/config",
        "payload": {
            "functions": ["їздити"],
            "subFunctions": {"їздити": "Колеса"},
            "budget": 5000,
            "weight": 800,
            "priority": "speed",
            "sensors": ["Сенсор відстані (УЗ)"],
            "terrain": "indoor",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.8, "force": 0.3, "economy": 0.5, "endurance": 0.4, "eco": 0.2},
            "eco_mode": False,
        },
        "expect": {
            "has_wheels": True,
            "has_motor": True,
            "has_hub": True,
            "has_power": True,
        },
    },
    {
        "name": "Квадрокоптер (Greedy)",
        "endpoint": "/config",
        "payload": {
            "functions": ["літати"],
            "subFunctions": {"літати": "Квадрокоптер"},
            "budget": 5000,
            "weight": 800,
            "priority": "speed",
            "sensors": [],
            "terrain": "outdoor_flat",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.5, "force": 0.5, "economy": 0.5, "endurance": 0.5, "eco": 0.25},
            "eco_mode": False,
        },
        "expect": {
            "has_propeller": True,
            "no_wing_plate": True,
            "has_motor": True,
            "has_hub": True,
        },
    },
    {
        "name": "Літак (Greedy)",
        "endpoint": "/config",
        "payload": {
            "functions": ["літати"],
            "subFunctions": {"літати": "Літак"},
            "budget": 5000,
            "weight": 800,
            "priority": "speed",
            "sensors": [],
            "terrain": "outdoor_flat",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.7, "force": 0.3, "economy": 0.4, "endurance": 0.5, "eco": 0.2},
            "eco_mode": False,
        },
        "expect": {
            "has_propeller": True,
            "has_wing": True,
            "has_motor": True,
            "has_hub": True,
        },
    },
    {
        "name": "Плаваючий робот (Greedy)",
        "endpoint": "/config",
        "payload": {
            "functions": ["плавати"],
            "subFunctions": {"плавати": "Гребні гвинти"},
            "budget": 5000,
            "weight": 800,
            "priority": "economy",
            "sensors": [],
            "terrain": "water_pool",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.3, "force": 0.3, "economy": 0.8, "endurance": 0.5, "eco": 0.3},
            "eco_mode": False,
        },
        "expect": {
            "has_water": True,
            "has_boat_hull": True,
            "has_motor": True,
            "has_hub": True,
        },
    },
    {
        "name": "Літак (Генетичний)",
        "endpoint": "/config/genetic",
        "payload": {
            "functions": ["літати"],
            "subFunctions": {"літати": "Літак"},
            "budget": 5000,
            "weight": 800,
            "priority": "speed",
            "sensors": [],
            "terrain": "outdoor_flat",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.7, "force": 0.3, "economy": 0.4, "endurance": 0.5, "eco": 0.2},
            "eco_mode": False,
        },
        "expect": {
            "has_propeller": True,
            "has_wing": True,
            "has_motor": True,
            "has_hub": True,
            "has_ga_stats": True,
        },
    },
    {
        "name": "Плаваючий робот (Генетичний)",
        "endpoint": "/config/genetic",
        "payload": {
            "functions": ["плавати"],
            "subFunctions": {"плавати": "Гребні гвинти"},
            "budget": 5000,
            "weight": 800,
            "priority": "economy",
            "sensors": [],
            "terrain": "water_pool",
            "sizeClass": "medium",
            "complexityLevel": 2,
            "powerProfile": "balanced",
            "decorationLevel": "normal",
            "weights": {"speed": 0.3, "force": 0.3, "economy": 0.8, "endurance": 0.5, "eco": 0.3},
            "eco_mode": False,
        },
        "expect": {
            "has_water": True,
            "has_boat_hull": True,
            "has_motor": True,
            "has_hub": True,
            "has_ga_stats": True,
        },
    },
]


def parse_sse_result(response):
    """Парсить SSE-відповідь від GA ендпоінту."""
    result = None
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            try:
                msg = json.loads(line[6:])
                if msg.get("type") == "result":
                    result = msg["result"]
            except:
                pass
    return result


def check_expectations(data, expect, parts):
    """Перевіряє очікування щодо конфігурації."""
    issues = []
    
    categories = [p.get("category", "") for p in parts]
    families = [p.get("family", "") for p in parts]
    names = [p.get("name", "") for p in parts]
    
    if expect.get("has_wheels") and "wheel" not in categories:
        issues.append("❌ Немає колес (wheel)")
    
    if expect.get("has_motor") and "motor" not in categories:
        issues.append("❌ Немає мотора (motor)")
    
    if expect.get("has_hub") and "controller" not in categories:
        issues.append("❌ Немає хабу/контролера (controller)")
    
    if expect.get("has_power") and "power" not in categories:
        issues.append("❌ Немає живлення (power)")
    
    if expect.get("has_propeller") and "propeller" not in categories:
        issues.append("❌ Немає пропелера (propeller)")
    
    if expect.get("has_wing"):
        has_wing = any("wing_plate" in f for f in families) or any("крило" in n.lower() for n in names)
        if not has_wing:
            issues.append("❌ Немає крил (wing_plate)")
    
    if expect.get("no_wing_plate"):
        has_wing = any("wing_plate" in f for f in families)
        if has_wing:
            issues.append("❌ Квадрокоптер має крила (wing_plate), не повинен!")
    
    if expect.get("has_water") and "water" not in categories:
        issues.append("❌ Немає водних деталей (water)")
    
    if expect.get("has_boat_hull"):
        has_hull = any("корпус" in n.lower() or "човен" in n.lower() for n in names)
        if not has_hull:
            issues.append("⚠️  Немає корпусу човна (можливо OK якщо є інші водні деталі)")
    
    if expect.get("has_ga_stats") and not data.get("ga_stats"):
        issues.append("❌ Немає GA статистики")
    
    return issues


def main():
    print("=" * 80)
    print("  ТЕСТ API КОНФІГУРАЦІЇ — ЯК ФРОНТЕНД НАДСИЛАЄ ЗАПИТИ")
    print("=" * 80)
    
    all_passed = True
    
    for scenario in USER_SCENARIOS:
        print(f"\n{'─' * 60}")
        print(f"  {scenario['name']}")
        print(f"{'─' * 60}")
        
        try:
            resp = requests.post(
                f"{BASE}{scenario['endpoint']}",
                json=scenario["payload"],
                timeout=120,
            )
            
            if resp.status_code != 200:
                print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")
                all_passed = False
                continue
            
            # Парсимо відповідь
            if scenario["endpoint"] == "/config/genetic":
                data = parse_sse_result(resp)
                if not data:
                    print(f"  ❌ Не вдалося отримати результат з SSE потоку")
                    all_passed = False
                    continue
            else:
                data = resp.json()
            
            if data.get("error"):
                print(f"  ❌ Помилка: {data['error']}")
                all_passed = False
                continue
            
            parts = data.get("selected", [])
            total_price = data.get("total_price", 0)
            total_weight = data.get("total_weight", 0)
            
            print(f"  Ціна: {total_price} ₴ | Вага: {total_weight} г | Деталей: {len(parts)}")
            
            # Виводимо компоненти по категоріях
            cats = {}
            for p in parts:
                cat = p.get("category", "?")
                if cat not in cats:
                    cats[cat] = []
                cats[cat].append(p)
            
            for cat in sorted(cats.keys()):
                items = cats[cat]
                names_str = ", ".join(set(p["name"] for p in items))
                print(f"    [{cat}] ({len(items)}): {names_str[:100]}")
            
            # GA stats
            if data.get("ga_stats"):
                gs = data["ga_stats"]
                print(f"    [GA] fitness={gs.get('final_fitness', '?')}, "
                      f"час={gs.get('elapsed_seconds', '?')}с, "
                      f"поколінь={gs.get('generations', '?')}")
            
            # Перевірка очікувань
            issues = check_expectations(data, scenario["expect"], parts)
            
            if issues:
                for iss in issues:
                    print(f"  {iss}")
                all_passed = False
            else:
                print(f"  ✅ Всі перевірки пройдені!")
            
            # Перевірка бюджету
            budget = scenario["payload"]["budget"]
            if total_price > budget:
                print(f"  ⚠️  Перевищення бюджету: {total_price} > {budget}")
            
            weight_limit = scenario["payload"]["weight"]
            if total_weight > weight_limit:
                print(f"  ⚠️  Перевищення ваги: {total_weight} > {weight_limit}")
            
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Сервер не відповідає! Запустіть: uvicorn app.main:app --reload")
            all_passed = False
        except Exception as e:
            print(f"  ❌ Помилка: {e}")
            all_passed = False
    
    print(f"\n{'=' * 80}")
    if all_passed:
        print("  ✅ ВСІ СЦЕНАРІЇ ПРОЙДЕНІ УСПІШНО!")
    else:
        print("  ⚠️  Деякі сценарії мають проблеми (дивіться вище)")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
