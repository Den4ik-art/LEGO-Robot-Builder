import React from "react";

interface FilterBarProps {
  categories: string[];
  selected: string;
  onSelect: (category: string) => void;
}

// 🔤 Мапа перекладів для категорій
const CATEGORY_LABELS: Record<string, string> = {
  all: "Всі",
  motor: "Мотори",
  sensor: "Сенсори",
  controller: "Контролери",
  power: "Живлення",
  wheel: "Колеса",
  tire: "Шини",
  tread: "Протектори",
  track: "Гусениці",
  propeller: "Пропелери",
  manipulator: "Маніпулятори",
  structure: "Конструкція",
  structure_kit: "Набори",
  accessory: "Аксесуари",
  water: "Водні",
};

const FilterBar: React.FC<FilterBarProps> = ({ categories, selected, onSelect }) => {
  return (
    <div className="w-full overflow-x-auto pb-2 no-scrollbar">
      <div className="flex flex-wrap gap-2 justify-center min-w-max px-2">
        {categories.map((cat) => {
          const label = CATEGORY_LABELS[cat] || cat; // Використовуємо переклад або оригінал
          const isSelected = selected === cat;

          return (
            <button
              key={cat}
              onClick={() => onSelect(cat)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ease-in-out border
                ${
                  isSelected
                    ? "bg-blue-600 text-white border-blue-600 shadow-md scale-105"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200"
                }
              `}
            >
              {label.charAt(0).toUpperCase() + label.slice(1)}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default FilterBar;