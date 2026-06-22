import React, { useState, useMemo } from "react";
import { useToast } from "../components/Toast";
import ComponentCard from "../components/ComponentCard";
import FilterBar from "../components/FilterBar";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaCar, FaPlane, FaWater, FaRobot, FaSearch,
  FaCoins, FaWeightHanging, FaTachometerAlt, FaShieldAlt, FaPiggyBank, FaDumbbell,
  FaTree, FaHome, FaSwimmingPool, FaMountain, FaMicrochip, FaPuzzlePiece, FaStar,
  FaDna, FaCogs, FaLeaf, FaBolt, FaFilePdf
} from "react-icons/fa";
import DownloadPDFButton from "../components/DownloadPDFButton";

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

type GaStats = {
  generations: number;
  population_size: number;
  final_fitness: number;
  elapsed_seconds: number;
  total_parts: number;
  best_fitness_history: number[];
  avg_fitness_history: number[];
};

type ApiResponse = {
  id?: number;
  selected: LegoComponent[];
  total_price: number;
  total_weight: number;
  remaining_budget: number;
  warning?: string;
  chromosome?: number[];
  ga_stats?: GaStats;
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
  { value: "indoor", label: "Приміщення", icon: <FaHome /> },
  { value: "outdoor_flat", label: "Вулиця (Рівно)", icon: <FaTree /> },
  { value: "offroad", label: "Off-road", icon: <FaMountain /> },
  { value: "water_pool", label: "Водойма", icon: <FaSwimmingPool /> },
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
    // Нові ваги пріоритетів (0.0 - 1.0)
    weights: {
      speed: 0.5,      // Швидкість
      force: 0.5,      // Сила
      economy: 0.5,    // Економія
      endurance: 0.5,  // Витривалість
      eco: 0.25,       // Еко (Енергоефективність)
    },
    eco_mode: false,   // Eco-mode toggle
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [algorithm, setAlgorithm] = useState<"sequential" | "genetic">("sequential");

  // Progress bar state for GA
  const [gaProgress, setGaProgress] = useState(0);
  const [gaTotal, setGaTotal] = useState(100);
  const [gaStatus, setGaStatus] = useState("");

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

  const handleWeightChange = (weightName: "speed" | "force" | "economy" | "endurance" | "eco", value: number) => {
    setFormData(prev => ({
      ...prev,
      weights: {
        ...prev.weights,
        [weightName]: value,
      },
    }));
  };

  // --- Сабміт ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.functions.length === 0) return showToast("Оберіть хоча б одну функцію!", "error");

    setLoading(true);
    setResult(null);
    setSelectedCategory("all");
    setGaProgress(0);
    setGaTotal(100);
    setGaStatus("Підготовка...");

    try {
      const token = localStorage.getItem("token");

      if (algorithm === "genetic") {
        // SSE-based request for GA with progress tracking
        const res = await fetch("http://127.0.0.1:8000/config/genetic", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
          body: JSON.stringify(formData),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Помилка генерації");
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        if (!reader) throw new Error("Не вдалося прочитати відповідь");

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events from buffer
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const msg = JSON.parse(line.substring(6));

                if (msg.type === "progress") {
                  setGaProgress(msg.progress);
                  setGaTotal(msg.total);
                  setGaStatus(msg.status || "");
                } else if (msg.type === "result") {
                  const data = msg.result;
                  if (data.error) {
                    throw new Error(data.error);
                  }
                  setResult(data);
                  if (data.warning) {
                    showToast(data.warning, "info");
                  } else {
                    showToast("Еволюцію завершено! Конфігурацію створено.", "success");
                  }
                } else if (msg.type === "error") {
                  throw new Error(msg.error);
                }
              } catch (parseErr) {
                // Ignore parse errors for incomplete lines
                if ((parseErr as Error).message !== "Unexpected end of JSON input") {
                  console.warn("SSE parse error:", parseErr);
                }
              }
            }
          }
        }
      } else {
        // Standard REST request for sequential
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

        if (data.warning) {
          showToast(data.warning, "info");
        } else {
          showToast("Конфігурацію успішно створено!", "success");
        }
      }

      if (window.innerWidth < 1024) {
        setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 100);
      }
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      setLoading(false);
      setGaProgress(0);
      setGaStatus("");
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
    <div className="min-h-screen w-full bg-[#facc15] font-sans text-slate-900 pb-20 relative overflow-x-hidden">
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          backgroundImage: `
            radial-gradient(circle at 14px 14px, #fef08a 3px, transparent 4px),
            radial-gradient(circle at 16px 16px, #ca8a04 6px, transparent 7px)
          `,
          backgroundSize: "32px 32px"
        }}
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            className="bg-white rounded-3xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#facc15] p-8 max-w-md mx-4 text-center w-full"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {algorithm === "genetic" ? (
              /* === GA Progress Bar Mode === */
              <>
                <div className="mb-4 flex justify-center">
                  <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center">
                    <FaDna className="text-2xl text-emerald-600 animate-pulse" />
                  </div>
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-1">
                  Генетична еволюція
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Алгоритм шукає оптимальну конфігурацію через еволюцію поколінь
                </p>

                {/* Progress Bar */}
                <div className="w-full bg-slate-200 rounded-full h-3 mb-2 overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-teal-500"
                    initial={{ width: "0%" }}
                    animate={{ width: `${gaTotal > 0 ? Math.round((gaProgress / gaTotal) * 100) : 0}%` }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs mb-3">
                  <span className="text-slate-500">
                    Покоління {gaProgress} / {gaTotal}
                  </span>
                  <span className="font-bold text-emerald-600">
                    {gaTotal > 0 ? Math.round((gaProgress / gaTotal) * 100) : 0}%
                  </span>
                </div>

                {gaStatus && (
                  <p className="text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2 border border-slate-100">
                    {gaStatus}
                  </p>
                )}
              </>
            ) : (
              /* === Sequential Spinner Mode === */
              <>
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
              </>
            )}
          </motion.div>
        </div>
      )}

      {/* Header Section (UI)*/}
      <div className="relative z-10 pt-10 pb-8 px-4 text-center">
        <div className="inline-block bg-white px-8 py-3 rounded-xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] mb-4 transform -skew-x-3">
          <h1 className="text-3xl md:text-5xl font-black italic uppercase text-slate-900 tracking-tighter">
            Спроектуй свого <span className="text-red-600 drop-shadow-[2px_2px_0px_#0f172a]">LEGO-Робота</span>
          </h1>
        </div>
        <br/>
        <p className="text-slate-900 font-bold bg-white/80 inline-block px-4 py-1 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] tracking-widest text-xs uppercase max-w-2xl mx-auto mt-2">
          Налаштуйте параметри середовища, функцій та обмеження бюджету — конфігуратор підбере оптимальний набір деталей.
        </p>
      </div>

      {/* Main Layout */}
      <div className="max-w-7xl mx-auto mt-6 px-4 grid grid-cols-1 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)] gap-6 items-start">

        {/* Left: Form Card */}
        <motion.div
          className="bg-white rounded-3xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] p-6 lg:sticky lg:top-6 relative z-10"
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
                      className={`text-left border-2 rounded-xl px-3 py-2 text-xs flex flex-col gap-1 transition-all ${isActive ? "border-blue-600 bg-blue-100 text-blue-900 shadow-[3px_3px_0px_0px_#2563eb] translate-y-0.5 translate-x-0.5" : "border-slate-900 bg-white shadow-[3px_3px_0px_0px_#0f172a] hover:bg-[#facc15]"
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
                          className="mt-1 text-xs w-full font-bold rounded-xl border-2 border-slate-900 bg-white px-2 py-1 shadow-[2px_2px_0px_0px_#0f172a] focus:outline-none"
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
                      className={`flex flex-col items-start gap-1 border-2 rounded-xl px-3 py-2 text-xs transition-all ${isActive
                        ? "border-emerald-600 bg-emerald-100 text-emerald-900 shadow-[3px_3px_0px_0px_#059669] translate-y-0.5 translate-x-0.5"
                        : "border-slate-900 bg-white shadow-[3px_3px_0px_0px_#0f172a] hover:bg-[#facc15]"
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
                  className="w-full text-xs font-bold rounded-xl border-2 border-slate-900 bg-white px-3 py-2 shadow-[3px_3px_0px_0px_#0f172a] focus:outline-none"
                >
                  <option value="small">Малий (S)</option>
                  <option value="medium">Середній (M)</option>
                  <option value="large">Великий (L)</option>
                </select>

                <select
                  name="powerProfile"
                  value={formData.powerProfile}
                  onChange={(e) => handlePriorityChange("powerProfile", e.target.value)}
                  className="w-full text-xs font-bold rounded-xl border-2 border-slate-900 bg-white px-3 py-2 shadow-[3px_3px_0px_0px_#0f172a] focus:outline-none"
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
                      className={`text-xs border-2 rounded-xl px-3 py-2 transition-all font-bold text-left ${isActive ? "border-amber-600 bg-amber-200 text-amber-900 shadow-[3px_3px_0px_0px_#d97706] translate-y-0.5 translate-x-0.5" : "border-slate-900 bg-white shadow-[3px_3px_0px_0px_#0f172a] hover:bg-[#facc15]"
                        }`}
                    >
                      {sensor}
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Ваги Пріоритетів */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaStar /> Ваги пріоритетів
              </h2>
              <p className="text-xs text-slate-500 mb-3">
                Налаштуйте важливість кожного критерію від 0.0 до 1.0
              </p>
              <div className="grid grid-cols-1 gap-3">
                <WeightSlider
                  icon={<FaTachometerAlt />}
                  label="Швидкість"
                  name="speed"
                  value={formData.weights.speed}
                  onChange={handleWeightChange}
                  color="blue"
                />
                <WeightSlider
                  icon={<FaShieldAlt />}
                  label="Сила (Крутний момент)"
                  name="force"
                  value={formData.weights.force}
                  onChange={handleWeightChange}
                  color="red"
                />
                <WeightSlider
                  icon={<FaPiggyBank />}
                  label="Економія (Ціна)"
                  name="economy"
                  value={formData.weights.economy}
                  onChange={handleWeightChange}
                  color="green"
                />
                <WeightSlider
                  icon={<FaDumbbell />}
                  label="Витривалість (Легкість)"
                  name="endurance"
                  value={formData.weights.endurance}
                  onChange={handleWeightChange}
                  color="purple"
                />
                <WeightSlider
                  icon={<FaBolt />}
                  label="Еко (Енергоефективність)"
                  name="eco"
                  value={formData.weights.eco}
                  onChange={handleWeightChange}
                  color="emerald"
                />
              </div>
            </section>

            {/* Eco-mode Toggle */}
            <section>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, eco_mode: !prev.eco_mode }))}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-black uppercase transition-all border-2 ${formData.eco_mode
                  ? "border-emerald-600 bg-emerald-100 text-emerald-900 shadow-[4px_4px_0px_0px_#059669] translate-y-1 translate-x-1"
                  : "border-slate-900 bg-white text-slate-900 shadow-[4px_4px_0px_0px_#0f172a] hover:bg-[#facc15]"
                  }`}
              >
                <span className="flex items-center gap-2">
                  <FaLeaf className={formData.eco_mode ? "text-emerald-500" : "text-slate-400"} />
                  <div className="text-left">
                    <div className="font-semibold">Eco-Mode</div>
                    <div className="text-[10px] opacity-70">Мінімізація енергоспоживання</div>
                  </div>
                </span>
                <div className={`w-10 h-5 rounded-full relative transition-colors ${formData.eco_mode ? "bg-emerald-500" : "bg-slate-300"
                  }`}>
                  <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all shadow ${formData.eco_mode ? "left-5" : "left-0.5"
                    }`} />
                </div>
              </button>
            </section>

            {/* Вибір алгоритму */}
            <section>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                <FaDna /> Алгоритм оптимізації
              </h2>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAlgorithm("sequential")}
                  className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all border-2 ${algorithm === "sequential"
                    ? "border-blue-600 bg-blue-100 text-blue-900 shadow-[3px_3px_0px_0px_#2563eb] translate-y-0.5 translate-x-0.5"
                    : "border-slate-900 bg-white text-slate-900 shadow-[3px_3px_0px_0px_#0f172a] hover:bg-[#facc15]"
                    }`}
                >
                  <FaCogs className="text-sm" />
                  <div className="text-left">
                    <div className="font-semibold">Послідовний</div>
                    <div className="text-[10px] opacity-70">Швидкий, детермінований</div>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setAlgorithm("genetic")}
                  className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all border-2 ${algorithm === "genetic"
                    ? "border-emerald-600 bg-emerald-100 text-emerald-900 shadow-[3px_3px_0px_0px_#059669] translate-y-0.5 translate-x-0.5"
                    : "border-slate-900 bg-white text-slate-900 shadow-[3px_3px_0px_0px_#0f172a] hover:bg-[#facc15]"
                    }`}
                >
                  <FaDna className="text-sm" />
                  <div className="text-left">
                    <div className="font-semibold">Генетичний</div>
                    <div className="text-[10px] opacity-70">Еволюційна оптимізація</div>
                  </div>
                </button>
              </div>
            </section>

            {/* Кнопка */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className={`w-full mt-2 font-black uppercase tracking-widest text-lg py-4 rounded-xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all flex items-center justify-center gap-3 disabled:opacity-60 disabled:cursor-not-allowed ${algorithm === "genetic"
                  ? "bg-emerald-500 text-white hover:bg-emerald-400"
                  : "bg-blue-600 text-white hover:bg-blue-500"
                  }`}
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {algorithm === "genetic" ? "Еволюція..." : "Обробка..."}
                  </>
                ) : (
                  <>
                    {algorithm === "genetic" ? <FaDna /> : <FaPuzzlePiece />}
                    {algorithm === "genetic" ? "Запустити еволюцію" : "Згенерувати конфігурацію"}
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Right: Results */}
        <motion.div
          id="results"
          className="bg-white rounded-3xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] p-6 relative z-10"
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
            {result && (
              <DownloadPDFButton
                configId={result.id}
                configData={{
                  id: result.id || 0,
                  request: formData,
                  result: { selected: result.selected, ga_stats: result.ga_stats },
                  total_price: result.total_price,
                  total_weight: result.total_weight,
                  remaining_budget: result.remaining_budget,
                  algorithm: algorithm === "genetic" ? "genetic" : "greedy",
                }}
              />
            )}
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-xs">
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

              {/* Використані ваги пріоритетів */}
              <div className="mb-6 p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <h3 className="text-xs font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <FaStar className="text-amber-500" /> Використані ваги пріоритетів
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <WeightDisplay label="Швидкість" value={formData.weights.speed} color="blue" icon={<FaTachometerAlt />} />
                  <WeightDisplay label="Сила" value={formData.weights.force} color="red" icon={<FaShieldAlt />} />
                  <WeightDisplay label="Економія" value={formData.weights.economy} color="green" icon={<FaPiggyBank />} />
                  <WeightDisplay label="Витривалість" value={formData.weights.endurance} color="purple" icon={<FaDumbbell />} />
                </div>
              </div>

              {/* GA Stats - тільки при генетичному алгоритмі */}
              {result.ga_stats && (
                <div className="mb-6 p-4 bg-emerald-50 rounded-2xl border border-emerald-200">
                  <h3 className="text-xs font-semibold text-emerald-700 mb-3 flex items-center gap-2">
                    <FaDna className="text-emerald-500" /> Статистика генетичного алгоритму
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="bg-white rounded-xl p-2.5 border border-emerald-100">
                      <div className="text-emerald-500 font-medium mb-1">Фітнес</div>
                      <div className="text-slate-900 font-bold text-sm">{result.ga_stats.final_fitness}</div>
                    </div>
                    <div className="bg-white rounded-xl p-2.5 border border-emerald-100">
                      <div className="text-emerald-500 font-medium mb-1">Поколінь</div>
                      <div className="text-slate-900 font-bold text-sm">{result.ga_stats.generations}</div>
                    </div>
                    <div className="bg-white rounded-xl p-2.5 border border-emerald-100">
                      <div className="text-emerald-500 font-medium mb-1">Час</div>
                      <div className="text-slate-900 font-bold text-sm">{result.ga_stats.elapsed_seconds}s</div>
                    </div>
                    <div className="bg-white rounded-xl p-2.5 border border-emerald-100">
                      <div className="text-emerald-500 font-medium mb-1">Популяція</div>
                      <div className="text-slate-900 font-bold text-sm">{result.ga_stats.population_size}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Попередження якщо є */}
              {result.warning && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-2xl text-sm text-blue-700">
                  <strong>ℹІнформація:</strong> {result.warning}
                </div>
              )}

              {/* Список деталей */}
              <div className="bg-white rounded-2xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] p-6">
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
              
              {/* Кнопка завантаження PDF */}
              <div className="mt-8 border-t-4 border-slate-900 pt-8 flex flex-col items-center">
                <div className="bg-[#facc15] px-6 py-2 rounded-xl border-4 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] transform -skew-x-2 mb-4">
                  <h3 className="text-xl font-black uppercase tracking-widest text-slate-900">ТЕХНІЧНА СПЕЦИФІКАЦІЯ</h3>
                </div>
                <p className="text-sm font-bold text-slate-600 mb-6 text-center max-w-md">
                  Отримайте повний перелік необхідних компонентів (BOM), розрахункову схему підключення вузлів та інженерні рекомендації щодо фізичного складання моделі.
                </p>
                <div className="w-full max-w-md">
                  <DownloadPDFButton
                    configId={result.id}
                    configData={{
                      id: result.id || 0,
                      request: formData,
                      result: { selected: result.selected, ga_stats: result.ga_stats },
                      total_price: result.total_price,
                      total_weight: result.total_weight,
                      remaining_budget: result.remaining_budget,
                      algorithm: algorithm === "genetic" ? "genetic" : "greedy",
                    }}
                    variant="large"
                  />
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
  <div className="bg-white p-3 rounded-xl border-2 border-slate-900 shadow-[3px_3px_0px_0px_#0f172a]">
    <div className="flex items-center justify-between mb-2">
      <span className="text-xs font-black uppercase tracking-wider text-slate-900 flex items-center gap-2">
        {icon} {label}
      </span>
      <span className="text-xs font-black text-blue-600 bg-blue-100 px-2 py-0.5 rounded border border-blue-600">
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
      className="w-full h-2 bg-slate-200 border border-slate-900 rounded-lg appearance-none cursor-pointer accent-blue-600"
    />
  </div>
);

const InfoBadge: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="border-2 border-slate-900 rounded-xl p-3 bg-white flex flex-col justify-center shadow-[3px_3px_0px_0px_#0f172a]">
    <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{label}</span>
    <span className="text-sm font-black text-slate-900">{value}</span>
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
  <div className="p-3 rounded-xl border-2 border-slate-900 bg-white shadow-[3px_3px_0px_0px_#0f172a]">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xs font-black uppercase tracking-wider text-slate-900 flex items-center gap-2">
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
            className={`text-[10px] font-black uppercase tracking-wider border-2 rounded-xl px-3 py-2 transition-all ${isActive
              ? "border-blue-600 bg-blue-100 text-blue-900 shadow-[2px_2px_0px_0px_#2563eb] translate-y-0.5 translate-x-0.5"
              : "border-slate-900 bg-white hover:bg-[#facc15] text-slate-900 shadow-[2px_2px_0px_0px_#0f172a]"
              }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  </div>
);

// --- Новий компонент для ваг пріоритетів ---
type WeightSliderProps = {
  icon: React.ReactNode;
  label: string;
  name: "speed" | "force" | "economy" | "endurance" | "eco";
  value: number;
  onChange: (name: "speed" | "force" | "economy" | "endurance" | "eco", value: number) => void;
  color: "blue" | "red" | "green" | "purple" | "emerald";
};

const WeightSlider: React.FC<WeightSliderProps> = ({ icon, label, name, value, onChange, color }) => {
  const colorClasses = {
    blue: { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-700", bar: "bg-blue-500" },
    red: { bg: "bg-red-50", border: "border-red-300", text: "text-red-700", bar: "bg-red-500" },
    green: { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-700", bar: "bg-emerald-500" },
    purple: { bg: "bg-purple-50", border: "border-purple-300", text: "text-purple-700", bar: "bg-purple-500" },
    emerald: { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-700", bar: "bg-emerald-500" },
  };

  const colors = colorClasses[color];
  const percentage = value * 100;

  return (
    <div className={`p-3 rounded-xl border-2 border-slate-900 bg-white shadow-[3px_3px_0px_0px_#0f172a]`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-black uppercase tracking-wider text-slate-900 flex items-center gap-2`}>
          {icon} {label}
        </span>
        <span className={`text-xs font-black ${colors.text} bg-white px-2 py-0.5 rounded border-2 border-slate-900`}>
          {value.toFixed(1)}
        </span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={0}
          max={1.0}
          step={0.1}
          value={value}
          onChange={(e) => onChange(name, Number(e.target.value))}
          className="w-full h-3 bg-slate-200 border-2 border-slate-900 rounded-lg appearance-none cursor-pointer"
        />
        <div
          className={`absolute top-0.5 left-0.5 h-2 ${colors.bar} rounded-lg pointer-events-none`}
          style={{ width: `calc(${percentage}% - 4px)` }}
        />
      </div>
      <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-2">
        <span>Не важливо</span>
        <span>Критично</span>
      </div>
    </div>
  );
};

// --- Компонент для відображення ваг у результатах ---
type WeightDisplayProps = {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: "blue" | "red" | "green" | "purple" | "emerald";
};

const WeightDisplay: React.FC<WeightDisplayProps> = ({ icon, label, value, color }) => {
  const colorClasses = {
    blue: { bg: "bg-blue-100", bar: "bg-blue-500", text: "text-blue-900" },
    red: { bg: "bg-red-100", bar: "bg-red-500", text: "text-red-900" },
    green: { bg: "bg-emerald-100", bar: "bg-emerald-500", text: "text-emerald-900" },
    purple: { bg: "bg-purple-100", bar: "bg-purple-500", text: "text-purple-900" },
    emerald: { bg: "bg-emerald-100", bar: "bg-emerald-500", text: "text-emerald-900" },
  };

  const colors = colorClasses[color];
  const percentage = ((value - 0.25) / 0.75) * 100;

  return (
    <div className="bg-white border-2 border-slate-900 rounded-xl p-2 shadow-[2px_2px_0px_0px_#0f172a]">
      <div className="flex items-center justify-between mb-2">
        <span className={`text-[10px] font-black uppercase tracking-wider ${colors.text} flex items-center gap-1`}>
          {icon} {label}
        </span>
        <span className={`text-xs font-black ${colors.text}`}>
          {value.toFixed(2)}
        </span>
      </div>
      <div className={`h-2 border border-slate-900 bg-slate-100 rounded-full overflow-hidden`}>
        <div
          className={`h-full ${colors.bar} rounded-full transition-all duration-300 border-r border-slate-900`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};