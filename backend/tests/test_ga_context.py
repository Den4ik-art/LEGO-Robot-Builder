"""
Test script: перевірка контекстної відповідності деталей.
Запускає GA для 3 різних конфігурацій і перевіряє,
що всі деталі відповідають обраним функціям.
"""
import json
import urllib.request
import sys

BASE = "http://127.0.0.1:8000/config/genetic"

test_cases = [
    {
        "name": "ЇЗДИТИ (ground only)",
        "payload": {
            "functions": ["їздити"],
            "subFunctions": {"їздити": "Колеса"},
            "budget": 3000,
            "weight": 1000,
            "priority": "speed",
            "sensors": [],
            "weights": {"speed": 0.7, "force": 0.5, "economy": 0.5, "endurance": 0.5},
        },
        "forbidden_domains": ["air", "water"],
    },
    {
        "name": "ЛІТАТИ (air only)",
        "payload": {
            "functions": ["літати"],
            "subFunctions": {"літати": "Квадрокоптер"},
            "budget": 5000,
            "weight": 1500,
            "priority": "speed",
            "sensors": [],
            "weights": {"speed": 0.8, "force": 0.6, "economy": 0.3, "endurance": 0.5},
        },
        "forbidden_domains": ["ground", "water"],
    },
    {
        "name": "ПЛАВАТИ (water only)",
        "payload": {
            "functions": ["плавати"],
            "subFunctions": {"плавати": "Гребні гвинти"},
            "budget": 4000,
            "weight": 1200,
            "priority": "stability",
            "sensors": [],
            "weights": {"speed": 0.4, "force": 0.7, "economy": 0.5, "endurance": 0.6},
        },
        "forbidden_domains": ["ground", "air"],
    },
]

def parse_sse_result(raw_text):
    """Parse SSE text to extract final result."""
    for line in raw_text.split("\n"):
        if line.startswith("data: "):
            try:
                msg = json.loads(line[6:])
                if msg.get("type") == "result":
                    return msg["result"]
            except:
                pass
    return None

print("=" * 60)
print("CONTEXT AWARENESS TEST")
print("=" * 60)

all_passed = True

for tc in test_cases:
    print(f"\n--- Test: {tc['name']} ---")
    try:
        req = urllib.request.Request(
            BASE,
            data=json.dumps(tc["payload"]).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        res = urllib.request.urlopen(req, timeout=120)
        raw = res.read().decode("utf-8")
        result = parse_sse_result(raw)

        if not result:
            print("  FAIL: No result in SSE stream")
            all_passed = False
            continue

        if "error" in result:
            print(f"  FAIL: GA error: {result['error']}")
            all_passed = False
            continue

        # Check domains
        parts = result.get("selected", [])
        violations = []
        neutral_cats = {"controller", "power", "sensor"}

        for part in parts:
            cat = part.get("category", "")
            domain = part.get("domain", "universal")
            if cat in neutral_cats:
                continue
            if domain in tc["forbidden_domains"]:
                violations.append(f"  !! {part.get('name')} (cat={cat}, domain={domain})")

        allowed = result.get("ga_stats", {}).get("allowed_domains", [])
        print(f"  Allowed domains: {allowed}")
        print(f"  Total parts: {len(parts)}")
        print(f"  Total price: {result.get('total_price')}")
        print(f"  Total weight: {result.get('total_weight')}")
        print(f"  Fitness: {result.get('ga_stats', {}).get('final_fitness')}")
        print(f"  Elapsed: {result.get('ga_stats', {}).get('elapsed_seconds')}s")

        if violations:
            print(f"  FAIL: {len(violations)} domain violations:")
            for v in violations[:5]:
                print(f"    {v}")
            all_passed = False
        else:
            print(f"  PASS: No domain violations!")

    except Exception as e:
        print(f"  ERROR: {e}")
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED")
print("=" * 60)
