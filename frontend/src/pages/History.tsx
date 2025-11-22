import React, { useEffect, useState } from "react";
import { useToast } from "../components/Toast";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FaHistory, FaTrash, FaCalendarAlt, FaRobot, 
  FaCoins, FaWeightHanging, FaMicrochip, FaChevronDown, FaChevronUp
} from "react-icons/fa";

// Тип компонента в історії
type HistoryComponent = {
  id: number;
  name: string;
  category: string;
  price: number;
  weight: number;
  quantity?: number; // Додаємо поле для кількості
};

interface HistoryEntry {
  username?: string;
  timestamp: string;
  request: {
    functions: string[];
    budget: number;
    weight: number;
    priority: string;
    sensors: number;
  };
  result: {
    selected: HistoryComponent[];
    total_price: number;
    total_weight: number;
  };
}

// --- Анімація ---
const listVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

// --- Допоміжна функція для групування ---
const aggregateComponents = (components: HistoryComponent[]) => {
  const map = new Map<number, HistoryComponent>();
  
  for (const comp of components) {
    const existing = map.get(comp.id);
    if (existing) {
      // Якщо деталь вже є, збільшуємо лічильник
      existing.quantity = (existing.quantity || 1) + 1;
    } else {
      // Якщо немає, додаємо з кількістю 1 (клонуємо об'єкт, щоб не мутувати оригінал)
      map.set(comp.id, { ...comp, quantity: 1 });
    }
  }
  
  return Array.from(map.values());
};

export default function History() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  
  const { showToast } = useToast();

  const fetchHistory = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/history/list", {
        headers: { "Content-Type": "application/json", token: token },
      });
      if (!res.ok) throw new Error("Помилка завантаження історії");
      const data = await res.json();
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearClick = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      showToast("Ви не авторизовані!", "error");
      return;
    }
    setShowConfirmModal(true);
  };

  const performClearHistory = async () => {
    const token = localStorage.getItem("token");
    setShowConfirmModal(false);

    try {
      const res = await fetch("http://127.0.0.1:8000/history/clear", {
        method: "DELETE",
        headers: { "Content-Type": "application/json", token: token || "" },
      });

      if (res.ok) {
        showToast("Історію успішно очищено ✅", "success");
        setHistory([]);
      } else {
        const data = await res.json();
        showToast(data.detail || "Помилка при очищенні історії ❌", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Помилка сервера ❌", "error");
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // --- Рендеринг стану завантаження ---
  if (loading)
    return (
      <div className="flex justify-center items-center min-h-[60vh] text-slate-500 animate-pulse gap-2">
        <FaRobot className="text-4xl" />
        <span className="text-xl font-medium">Завантаження архіву...</span>
      </div>
    );

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 font-sans text-slate-800">
      <div className="max-w-4xl mx-auto">
        
        {/* === HEADER === */}
        <div className="flex flex-col sm:flex-row justify-between items-center mb-10 gap-4">
          <div className="text-center sm:text-left">
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight mb-2 flex items-center justify-center sm:justify-start gap-3">
              <FaHistory className="text-blue-600" />
              Історія <span className="text-slate-500 font-normal">конфігурацій</span>
            </h1>
            <p className="text-slate-500">Переглядайте та аналізуйте ваші попередні проєкти.</p>
          </div>

          {history.length > 0 && (
            <button
              onClick={handleClearClick}
              className="flex items-center gap-2 px-5 py-2.5 bg-white border border-red-200 text-red-600 font-bold rounded-xl hover:bg-red-50 hover:border-red-300 transition-all shadow-sm hover:shadow-md active:scale-95"
            >
              <FaTrash size={14} /> Очистити все
            </button>
          )}
        </div>

        {/* === СПИСОК === */}
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border-2 border-dashed border-slate-200">
            <div className="bg-blue-50 p-6 rounded-full mb-4">
              <FaRobot className="text-5xl text-blue-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-400 mb-2">Історія порожня</h3>
            <p className="text-slate-400 text-sm">Створіть свого першого робота у Конфігураторі!</p>
          </div>
        ) : (
          <motion.div 
            className="space-y-6"
            variants={listVariants}
            initial="hidden"
            animate="visible"
          >
            {history.slice().reverse().map((entry, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className={`bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden transition-all duration-300 hover:shadow-md
                  ${expanded === index ? "ring-2 ring-blue-500/20" : ""}
                `}
              >
                {/* --- Верхня частина картки (Завжди видима) --- */}
                <div 
                  className="p-5 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
                  onClick={() => setExpanded(expanded === index ? null : index)}
                >
                  <div className="flex gap-4 items-start">
                    <div className="p-3 bg-blue-100 text-blue-600 rounded-xl hidden sm:block">
                      <FaRobot size={24} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
                        <FaCalendarAlt size={12} />
                        {new Date(entry.timestamp).toLocaleString("uk-UA", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </div>
                      <h3 className="text-lg font-bold text-slate-800 mb-1 capitalize">
                        {entry.request.functions.length > 0 
                          ? entry.request.functions.join(" + ") 
                          : "Базова конфігурація"}
                      </h3>
                      <div className="flex gap-2">
                         <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-medium">
                           {entry.result.selected.length} деталей
                         </span>
                         <span className={`text-xs px-2 py-0.5 rounded font-medium bg-green-100 text-green-700`}>
                           {entry.result.total_price} ₴
                         </span>
                      </div>
                    </div>
                  </div>
                  
                  <button className="text-slate-400 hover:text-blue-600 transition-colors p-2">
                    {expanded === index ? <FaChevronUp /> : <FaChevronDown />}
                  </button>
                </div>

                {/* --- Нижня частина (Деталі) --- */}
                <AnimatePresence>
                  {expanded === index && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-slate-100 bg-slate-50/30"
                    >
                      <div className="p-6">
                        
                        {/* Метрики запиту */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                          <MetricBox label="Бюджет" value={`${entry.request.budget} ₴`} icon={<FaCoins/>} color="text-yellow-600 bg-yellow-50"/>
                          <MetricBox label="Макс. Вага" value={`${entry.request.weight} г`} icon={<FaWeightHanging/>} color="text-blue-600 bg-blue-50"/>
                          <MetricBox label="Пріоритет" value={entry.request.priority} icon={<FaMicrochip/>} color="text-purple-600 bg-purple-50" capitalize/>
                          <MetricBox label="Сенсори" value={`${entry.request.sensors} шт`} icon={<FaRobot/>} color="text-indigo-600 bg-indigo-50"/>
                        </div>

                        {/* Список компонентів (ЗГРУПОВАНИЙ) */}
                        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                          <div className="px-4 py-3 bg-slate-100 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wide flex justify-between">
                            <span>Деталь</span>
                            <span>К-сть / Ціна / Вага</span>
                          </div>
                          <ul className="divide-y divide-slate-100">
                            {aggregateComponents(entry.result.selected).map((comp) => (
                              <li key={comp.id} className="px-4 py-3 flex justify-between items-center hover:bg-slate-50 transition-colors">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-slate-800">{comp.name}</span>
                                    {/* Бейдж кількості */}
                                    {(comp.quantity || 1) > 1 && (
                                      <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                        ×{comp.quantity}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-400 capitalize">{comp.category}</p>
                                </div>
                                <div className="text-right text-xs font-medium text-slate-600">
                                  <p>
                                    {comp.price * (comp.quantity || 1)} ₴ 
                                    {(comp.quantity || 1) > 1 && <span className="text-slate-400 font-normal ml-1">({comp.price} шт)</span>}
                                  </p>
                                  <p className="text-slate-400">
                                    {Number((comp.weight * (comp.quantity || 1)).toFixed(1))} г
                                  </p>
                                </div>
                              </li>
                            ))}
                          </ul>
                          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex justify-between items-center font-bold text-sm text-slate-800">
                            <span>Всього</span>
                            <div className="text-right">
                              <span className="text-green-600 mr-3">{entry.result.total_price} ₴</span>
                              <span className="text-blue-600">{entry.result.total_weight} г</span>
                            </div>
                          </div>
                        </div>

                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* ✨ КАСТОМНЕ МОДАЛЬНЕ ВІКНО ✨ */}
      <AnimatePresence>
        {showConfirmModal && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm px-4"
          >
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full text-center"
            >
              <div className="mx-auto w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mb-6 text-2xl">
                <FaTrash />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">Очистити історію?</h3>
              <p className="text-slate-500 text-sm mb-8">
                Ви впевнені, що хочете видалити всі записи? Цю дію неможливо скасувати.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 py-3 bg-white border border-slate-300 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition"
                >
                  Скасувати
                </button>
                <button
                  onClick={performClearHistory}
                  className="flex-1 py-3 bg-red-600 text-white font-semibold rounded-xl hover:bg-red-700 transition shadow-lg shadow-red-500/30"
                >
                  Так, видалити
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Допоміжний компонент для метрик
const MetricBox = ({ label, value, icon, color, capitalize }: any) => (
  <div className="flex items-center gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
    <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
    <div>
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</p>
      <p className={`text-sm font-bold text-slate-800 ${capitalize ? "capitalize" : ""}`}>{value}</p>
    </div>
  </div>
);