import React, { useState, useMemo } from "react";
import { useToast } from "../components/Toast";
import ComponentCard from "../components/ComponentCard";
import FilterBar from "../components/FilterBar";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FaCar, FaPlane, FaWater, FaRobot, FaSearch, 
  FaCoins, FaWeightHanging, FaTachometerAlt, FaShieldAlt, FaPiggyBank, FaDumbbell,
  FaTree, FaHome, FaSwimmingPool, FaMountain, FaMicrochip, FaPuzzlePiece, FaStar
} from "react-icons/fa";

// --- Типи ---
type LegoComponent = {
  id: number;
  unique_id?: string;
  name: string;
  category: string;
  price: number;
  weight: number;
  image?: string;
  quantity?: number;
};

type ApiResponse = {
  selected: LegoComponent[];
  total_price: number;
  total_weight: number;
  remaining_budget: number;
  warning?: string;
};

// --- Опції функцій ---
const FUNCTION_OPTIONS = [
  { id: "їздити", label: "Їздити", icon: <FaCar />, subtypes: ["Колеса", "Гусениці"] },
  { id: "літати", label: "Літати", icon: <FaPlane />, subtypes: ["Квадрокоптер", "Вертоліт", "Літак"] },
  { id: "плавати", label: "Плавати", icon: <FaWater />, subtypes: ["Гребні гвинти", "Водомет", "Плавники"] },
  { id: "маніпулювати", label: "Маніпулювати", icon: <FaRobot />, subtypes: ["Клішня (Захват)", "Лінійний актуатор", "Біонічна рука"] },
  { id: "сканувати", label: "Сканувати", icon: <FaSearch />, subtypes: [] },
];

const TERRAIN_OPTIONS = [
  { value: "indoor",       label: "Приміщення",       icon: <FaHome /> },
  { value: "outdoor_flat", label: "Вулиця (Рівно)",   icon: <FaTree /> },
  { value: "offroad",      label: "Off-road",         icon: <FaMountain /> },
  { value: "water_pool",   label: "Водойма",          icon: <FaSwimmingPool /> },
];

const SENSORS_LIST = [
  "Сенсор відстані (УЗ)", "Сенсор кольору", "Сенсор дотику",
  "Гіроскоп", "Камера (AI Vision)", "Лідар (Laser)", "GPS Модуль",
  "Сенсор відстані (EV3)", "Сенсор кольору (NXT)", "Датчик світла (NXT)",
];

export default function Configurator() {
  const { showToast } = useToast();

  const [formData, setFormData] = useState({
    functions: [] as string[],
    subFunctions: {} as Record<string, string>,
    budget: 1500,
    weight: 500,
    priority: "speed",
    sensors: [] as string[],
    terrain: "indoor",
    sizeClass: "medium",
    complexityLevel: 2,
    powerProfile: "balanced",
    decorationLevel: "normal",
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // --- Обробники форми ---
  
  const handleFunctionToggle = (funcId: string) => {
    setFormData(prev => {
      const exists = prev.functions.includes(funcId);
      const newFunctions = exists
        ? prev.functions.filter((f) => f !== funcId)
        : [...prev.functions, funcId];
      
      const newSub = { ...prev.subFunctions };
      if (exists) delete newSub[funcId];
      else {
        const opt = FUNCTION_OPTIONS.find(o => o.id === funcId);
        if (opt?.subtypes.length) newSub[funcId] = opt.subtypes[0];
      }
      return { ...prev, functions: newFunctions, subFunctions: newSub };
    });
  };

  const handleSubFunctionChange = (funcId: string, subtype: string) => {
    setFormData(prev => ({
      ...prev,
      subFunctions: { ...prev.subFunctions, [funcId]: subtype },
    }));
  };
  
  const handleTerrainChange = (terrain: string) => {
    setFormData(prev => ({ ...prev, terrain }));
  };

  const handleSliderChange = (name: "budget" | "weight" | "complexityLevel", value: number) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSensorToggle = (s: string) => {
    setFormData(prev => {
      const exists = prev.sensors.includes(s);
      return {
        ...prev,
        sensors: exists
          ? prev.sensors.filter(i => i !== s) 
          : [...prev.sensors, s]
      };
    });
  };

  const handlePriorityChange = (name: "powerProfile" | "decorationLevel" | "priority" | "sizeClass", value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // --- Сабміт ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.functions.length === 0) return showToast("Оберіть хоча б одну функцію!", "error");
    
    setLoading(true);
    setResult(null);
    setSelectedCategory("all");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://127.0.0.1:8000/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || data.detail || "Помилка генерації");
      }
      
      setResult(data);
      
      // Показуємо попередження якщо воно є
      if (data.warning) {
        showToast(data.warning, "info");
      } else {
        showToast("Конфігурацію успішно створено!", "success");
      }
      
      if (window.innerWidth < 1024) {
        setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 100);
      }
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      setLoading(false);
    }
  };

  // Групування компонентів
  const aggregatedComponents = useMemo(() => {
    if (!result?.selected) return [];
    const map = new Map<number, LegoComponent>();
    for (const comp of result.selected) {
      const existing = map.get(comp.id);
      if (existing) existing.quantity = (existing.quantity || 1) + 1;
      else map.set(comp.id, { ...comp, quantity: 1 });
    }
    return Array.from(map.values());
  }, [result]);

  const displayedComponents = selectedCategory !== "all"
    ? aggregatedComponents.filter((c) => c.category === selectedCategory)
    : aggregatedComponents;
    
  const categories = aggregatedComponents.length 
    ? ["all", ...new Set(aggregatedComponents.map(c => c.category))]
    : [];

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800 pb-20">
      
      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <motion.div 
            className="bg-white rounded-3xl shadow-2xl p-8 max-w-md mx-4 text-center"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="mb-4 flex justify-center">
              <div className="relative">
                <div className="w-20 h-20 border-4 border-blue-200 rounded-full"></div>
                <div className="w-20 h-20 border-4 border-blue-600 border-t-transparent rounded-full animate-spin absolute top-0 left-0"></div>
              </div>
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">
              Генеруємо конфігурацію...
            </h3>
            <p className="text-sm text-slate-600 mb-4">
              Алгоритм підбирає оптимальний набір деталей для вашого робота
            </p>
            <div className="flex items-center justify-center gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-blue-600 rounded-full"
                  animate={{
                    y: [0, -10, 0],
                    opacity: [1, 0.5, 1]
                  }}
                  transition={{
                    duration: 0.6,
                    repeat: Infinity,
                    delay: i * 0.2
                  }}
                />
              ))}
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Header Section (UI)*/}
      <div className="bg-white border-b border-slate-200 pt-10 pb-8 px-4 shadow-sm">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mb-3">
            Спроектуй свого <span className="text-blue-600">LEGO-Робота</span>
          </h1>
          <p className="text-slate-500 text-lg max-w-2xl mx-auto">
            Налаштуйте параметри середовища, функцій та обмеження бюджету — конфігуратор підбере оптимальний набір деталей.
          </p>
        </div>
      </div>

      {/* Main Layout */}
      <div className="max-w-7xl mx-auto mt-6 px-4 grid grid-cols-1 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)] gap-6 items-start">
        
        {/* Left: Form Card */}
        <motion.div
          className="bg-white rounded-3xl shadow-md border border-slate-200 p-6 lg:sticky lg:top-6"
          initial={{ opacity: 0, x: -15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
        >
          <form className="space-y-6" onSubmit={handleSubmit}>
            
            {/* Функції */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaRobot /> Функції робота
              </h2>
              <p className="text-xs text-slate-500 mb-3">
                Оберіть, що повинен робити робот. Для деяких функцій можна обрати конкретну реалізацію.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {FUNCTION_OPTIONS.map((f) => {
                  const isActive = formData.functions.includes(f.id);
                  return (
                    <div
                      key={f.id}
                      className={`text-left border rounded-2xl px-3 py-2 text-xs flex flex-col gap-1 transition ${
                        isActive ? "border-blue-500 bg-blue-50 text-blue-700 shadow-sm" : "border-slate-200 bg-slate-50 hover:bg-slate-100"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => handleFunctionToggle(f.id)}
                        className="w-full text-left flex items-center justify-between"
                      >
                        <span className="flex items-center gap-2">
                          <span className="text-base">{f.icon}</span>
                          <span className="font-semibold">{f.label}</span>
                        </span>
                        <input
                          type="checkbox"
                          checked={isActive}
                          readOnly
                          className="w-4 h-4 text-blue-600 rounded"
                        />
                      </button>

                      {isActive && f.subtypes.length > 0 && (
                        <select
                          className="mt-1 text-xs w-full rounded-xl border border-slate-200 bg-white px-2 py-1"
                          value={formData.subFunctions[f.id] || f.subtypes[0]}
                          onChange={(e) => handleSubFunctionChange(f.id, e.target.value)} 
                        >
                          {f.subtypes.map((sub) => (
                            <option key={sub} value={sub}>
                              {sub}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Середовище */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaTree /> Середовище
              </h2>
              <p className="text-xs text-slate-500 mb-3">
                Де ваш робот буде працювати найчастіше?
              </p>
              <div className="grid grid-cols-2 gap-3">
                {TERRAIN_OPTIONS.map((t) => {
                  const isActive = formData.terrain === t.value;
                  return (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => handleTerrainChange(t.value)}
                      className={`flex flex-col items-start gap-1 border rounded-2xl px-3 py-2 text-xs transition ${
                        isActive
                          ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm"
                          : "border-slate-200 bg-slate-50 hover:bg-slate-100"
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-base">{t.icon}</span>
                        <span className="font-semibold">{t.label}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Бюджет, вага, складність */}
            <section className="grid grid-cols-1 gap-3">
              <SliderBlock
                icon={<FaCoins />}
                label="Бюджет (грн)"
                name="budget"
                min={100}
                max={50000}
                step={50}
                value={formData.budget}
                onChange={handleSliderChange}
              />
              <SliderBlock
                icon={<FaWeightHanging />}
                label="Максимальна вага (г)"
                name="weight"
                min={100}
                max={4000}
                step={50}
                value={formData.weight}
                onChange={handleSliderChange}
              />
              <SliderBlock
                icon={<FaTachometerAlt />}
                label="Рівень складності"
                name="complexityLevel"
                min={1}
                max={3}
                step={1}
                value={formData.complexityLevel}
                onChange={handleSliderChange}
              />
            </section>

            {/* Розмір */}
            <section>
              <h2 className="text-sm font-semibold text-slate-900 mb-2">
                Розмір / Профіль
              </h2>
              <div className="flex gap-3">
                <select 
                  name="sizeClass" 
                  value={formData.sizeClass} 
                  onChange={(e) => handlePriorityChange("sizeClass", e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
                >
                  <option value="small">Малий (S)</option>
                  <option value="medium">Середній (M)</option>
                  <option value="large">Великий (L)</option>
                </select>

                <select 
                  name="powerProfile" 
                  value={formData.powerProfile} 
                  onChange={(e) => handlePriorityChange("powerProfile", e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
                >
                  <option value="long_runtime">Еко (Довгий час)</option>
                  <option value="balanced">Збалансовано</option>
                  <option value="performance">Турбо (Потужність)</option>
                </select>
              </div>
            </section>

            {/* Сенсори */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaMicrochip /> Сенсори ({formData.sensors.length})
              </h2>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto pr-1">
                {SENSORS_LIST.map((sensor) => {
                  const isActive = formData.sensors.includes(sensor);
                  return (
                    <button
                      key={sensor}
                      type="button"
                      onClick={() => handleSensorToggle(sensor)}
                      className={`text-xs border rounded-2xl px-3 py-2 transition text-left ${
                        isActive ? "border-amber-500 bg-amber-50 text-amber-700 shadow-sm" : "border-slate-200 bg-slate-50 hover:bg-slate-100"
                      }`}
                    >
                      {sensor}
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Пріоритет */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaShieldAlt /> Пріоритет
              </h2>
              <div className="grid grid-cols-2 gap-2">
                {["speed", "stability", "cheapness", "durability"].map((p) => {
                  const isActive = formData.priority === p;
                  const label = { speed: "Швидкість", stability: "Сила", cheapness: "Економія", durability: "Витривалість" }[p] || p;
                  const icon = { speed: <FaTachometerAlt />, stability: <FaShieldAlt />, cheapness: <FaPiggyBank />, durability: <FaDumbbell /> }[p];

                  return (
                    <button
                      key={p}
                      type="button"
                      onClick={() => handlePriorityChange("priority", p)}
                      className={`flex-1 py-2 text-[10px] font-bold uppercase rounded-2xl flex flex-col items-center gap-1 transition-all border
                        ${isActive ? "border-purple-500 bg-purple-50 text-purple-700 shadow-sm" : "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600"}`}
                    >
                      <span className="text-sm">{icon}</span>
                      {label}
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Кнопка */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-3 px-4 shadow-lg flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed transition"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Обробка...
                  </>
                ) : (
                  <>
                    <FaPuzzlePiece />
                    Згенерувати конфігурацію
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Right: Results */}
        <motion.div
          id="results"
          className="bg-white rounded-3xl shadow-md border border-slate-200 p-6"
          initial={{ opacity: 0, x: 15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25 }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <FaPuzzlePiece /> Результат підбору
              </h2>
              <p className="text-xs text-slate-500">
                Перегляньте підібрані деталі та оберіть потрібну категорію.
              </p>
            </div>
          </div>

          <div className="mb-6">
            <FilterBar categories={categories} selected={selectedCategory} onSelect={setSelectedCategory} />
          </div>

          {!result && (
            <div className="border border-dashed border-slate-200 rounded-3xl p-10 text-center text-slate-400 text-sm">
              Згенеруйте конфігурацію, щоб побачити підібрані деталі.
            </div>
          )}

          {result && (
            <>
              {/* Загальна інформація */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6 text-xs">
                <InfoBadge
                  label="Кількість типів деталей"
                  value={aggregatedComponents.length.toString()}
                />
                <InfoBadge
                  label="Сумарна ціна"
                  value={`${result.total_price.toFixed(2)} грн`}
                />
                <InfoBadge
                  label="Сумарна вага"
                  value={`${result.total_weight.toFixed(1)} г`}
                />
                <InfoBadge
                  label="Залишок бюджету"
                  value={`${result.remaining_budget.toFixed(2)} грн`}
                />
              </div>

              {/* Попередження якщо є */}
              {result.warning && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-2xl text-sm text-blue-700">
                  <strong>ℹІнформація:</strong> {result.warning}
                </div>
              )}

              {/* Список деталей */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                  <AnimatePresence mode="popLayout">
                    {displayedComponents.map((comp) => (
                      <motion.div 
                        key={comp.id}
                        layout
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        transition={{ type: "spring", stiffness: 300, damping: 25 }}
                      >
                        <ComponentCard component={comp} quantity={comp.quantity} />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}

// --- UI Components Helpers ---

const SliderBlock: React.FC<{
  icon: React.ReactNode;
  label: string;
  name: "budget" | "weight" | "complexityLevel";
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (name: any, value: number) => void;
}> = ({ icon, label, name, min, max, step, value, onChange }) => (
  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
    <div className="flex items-center justify-between mb-1">
      <span className="text-xs font-semibold text-slate-700 flex items-center gap-2">
        {icon} {label}
      </span>
      <span className="text-xs font-semibold text-blue-600">
        {value} {name === "budget" ? "грн" : name === "weight" ? "г" : "lvl"}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(name, Number(e.target.value))}
      className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-600 transition-all"
    />
  </div>
);

const InfoBadge: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="border border-slate-200 rounded-xl p-3 bg-white flex flex-col justify-center shadow-sm">
    <span className="text-[10px] text-slate-500 font-medium">{label}</span>
    <span className="text-sm font-semibold text-slate-800">{value}</span>
  </div>
);

type PrioritySelectProps = {
  icon: React.ReactNode;
  label: string;
  name: "priority" | "decorationLevel" | "powerProfile";
  value: string;
  options: { value: string; label: string }[];
  onChange: (name: any, value: string) => void;
};

const PrioritySelect: React.FC<PrioritySelectProps> = ({
  icon,
  label,
  name,
  value,
  options,
  onChange,
}) => (
  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-xs font-semibold text-slate-700 flex items-center gap-2">
        {icon} {label}
      </span>
    </div>
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const isActive = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(name, opt.value)}
            className={`text-[10px] font-bold uppercase border rounded-xl px-3 py-2 transition ${
              isActive
                ? "border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm"
                : "border-slate-200 bg-white hover:bg-slate-100 text-slate-600"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  </div>
);