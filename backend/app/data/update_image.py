import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

original_path = os.path.join(BASE_DIR, "lego_components copy.json")
current_path = os.path.join(BASE_DIR, "lego_components.json")

print("Loading files...")

with open(original_path, "r", encoding="utf-8") as f:
    original = json.load(f)

with open(current_path, "r", encoding="utf-8") as f:
    current = json.load(f)

# Створюємо мапу старих зображень
image_by_id = {item["id"]: item["image"] for item in original}

updated = 0

for item in current:
    old_img = image_by_id.get(item["id"])
    if old_img:
        item["image"] = old_img
        updated += 1

with open(current_path, "w", encoding="utf-8") as f:
    json.dump(current, f, ensure_ascii=False, indent=2)

print(f"✔️ Completed successfully! Updated {updated} images.")
