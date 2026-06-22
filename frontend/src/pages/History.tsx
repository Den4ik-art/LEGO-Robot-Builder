import React, { useEffect, useState } from "react";
import { useToast } from "../components/Toast";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FaHistory, FaTrash, FaCalendarAlt, FaRobot, 
  FaCoins, FaWeightHanging, FaMicrochip, FaChevronDown, FaChevronUp
} from "react-icons/fa";

import DownloadPDFButton from "../components/DownloadPDFButton";

// Тип компонента в історії
type HistoryComponent = {
  id: number;
  name: string;
  category: string;
  price: number;
  weight: number;
  quantity?: number;
};

interface HistoryEntry {
  id: number;
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
      existing.quantity = (existing.quantity || 1) + 1;
    } else {
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
        showToast("Історію успішно очищено", "success");
        setHistory([]);
      } else {
        const data = await res.json();
        showToast(data.detail || "Помилка при очищенні історії", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Помилка сервера", "error");
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const bgPattern = {
    backgroundImage: `radial-gradient(circle at 14px 14px, #fef08a 3px, transparent 4px), radial-gradient(circle at 16px 16px, #ca8a04 6px, transparent 7px)`,
    backgroundSize: "32px 32px"
  };

  // --- Рендеринг стану завантаження ---
  if (loading)
    return (
      <div className="min-h-screen bg-[#facc15] flex flex-col items-center justify-center">
        <div className="relative w-20 h-20 bg-white border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] rounded-2xl flex items-center justify-center animate-bounce">
          <FaRobot className="text-4xl text-blue-600 animate-pulse" />
        </div>
        <p className="mt-6 text-slate-900 font-black uppercase tracking-widest bg-white px-4 py-1 border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] rounded-lg">Завантаження...</p>
      </div>
    );

  return (
    <div className="min-h-screen bg-[#facc15] py-12 px-4 sm:px-6 lg:px-8 font-sans text-slate-900 relative overflow-x-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-40" style={bgPattern} />
      
      <div className="max-w-4xl mx-auto relative z-10">
        
        {/* HEADER */}
        <div className="flex flex-col sm:flex-row justify-between items-center mb-10 gap-6">
          <div className="text-center sm:text-left">
            <div className="inline-block bg-white px-6 py-2 rounded-xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] transform -skew-x-3 mb-4">
              <h1 className="text-3xl md:text-4xl font-black italic uppercase text-slate-900 tracking-tighter flex items-center gap-3">
                <FaHistory className="text-blue-600 drop-shadow-[2px_2px_0px_#0f172a]" />
                Історія <span className="text-red-600 drop-shadow-[2px_2px_0px_#0f172a]">конфігурацій</span>
              </h1>
            </div>
            <p className="text-slate-900 font-black uppercase tracking-widest text-sm bg-white/80 backdrop-blur-sm inline-block px-4 py-1 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">
              Переглядайте та аналізуйте ваші попередні проєкти
            </p>
          </div>

          {history.length > 0 && (
            <button
              onClick={handleClearClick}
              className="flex items-center gap-2 px-6 py-3 bg-red-500 border-4 border-slate-900 text-white font-black uppercase tracking-widest rounded-xl hover:bg-red-600 shadow-[6px_6px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all"
            >
              <FaTrash size={16} /> Очистити все
            </button>
          )}
        </div>

        {/* СПИСОК */}
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] text-center">
            <div className="bg-blue-100 p-6 rounded-2xl border-4 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] mb-6">
              <FaRobot className="text-5xl text-blue-500" />
            </div>
            <h3 className="text-2xl font-black uppercase tracking-widest text-slate-900 mb-2">Історія порожня</h3>
            <p className="text-slate-500 font-bold uppercase tracking-wider text-sm">Створіть свого першого робота у Конфігураторі!</p>
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
                className={`bg-white rounded-2xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] overflow-hidden transition-all duration-300
                  ${expanded === index ? "translate-y-1 translate-x-1 shadow-[4px_4px_0px_0px_#0f172a]" : ""}
                `}
              >
                {/* --- Верхня частина картки --- */}
                <div 
                  className="p-5 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 cursor-pointer hover:bg-slate-50 transition-colors"
                  onClick={() => setExpanded(expanded === index ? null : index)}
                >
                  <div className="flex gap-4 items-start">
                    <div className="p-3 bg-blue-500 text-white rounded-xl border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] hidden sm:block">
                      <FaRobot size={24} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-500 mb-2">
                        <FaCalendarAlt size={12} />
                        {new Date(entry.timestamp).toLocaleString("uk-UA", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </div>
                      <h3 className="text-xl font-black uppercase text-slate-900 mb-2">
                        {entry.request.functions.length > 0 
                          ? entry.request.functions.join(" + ") 
                          : "Базова конфігурація"}
                      </h3>
                      <div className="flex gap-2">
                         <span className="text-xs px-2 py-1 bg-slate-100 text-slate-900 font-black uppercase tracking-wider rounded border-2 border-slate-900">
                           {entry.result.selected.length} деталей
                         </span>
                         <span className={`text-xs px-2 py-1 rounded font-black uppercase tracking-wider bg-green-500 text-white border-2 border-slate-900`}>
                           {entry.result.total_price} ₴
                         </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <DownloadPDFButton configId={entry.id} />
                    <button className="text-slate-900 bg-slate-100 p-2 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] hover:bg-[#facc15] transition-all">
                      {expanded === index ? <FaChevronUp /> : <FaChevronDown />}
                    </button>
                  </div>
                </div>

                {/* --- Нижня частина (Деталі) --- */}
                <AnimatePresence>
                  {expanded === index && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t-4 border-slate-900 bg-slate-50"
                    >
                      <div className="p-6">
                        
                        {/* Метрики запиту */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                          <MetricBox label="Бюджет" value={`${entry.request.budget} ₴`} icon={<FaCoins/>} color="bg-yellow-400"/>
                          <MetricBox label="Макс. Вага" value={`${entry.request.weight} г`} icon={<FaWeightHanging/>} color="bg-blue-400"/>
                          <MetricBox label="Пріоритет" value={entry.request.priority} icon={<FaMicrochip/>} color="bg-purple-400" capitalize/>
                          <MetricBox label="Сенсори" value={`${entry.request.sensors} шт`} icon={<FaRobot/>} color="bg-emerald-400"/>
                        </div>

                        {/* Список компонентів */}
                        <div className="bg-white rounded-xl border-4 border-slate-900 overflow-hidden shadow-[4px_4px_0px_0px_#0f172a]">
                          <div className="px-4 py-3 bg-slate-900 text-white text-xs font-black uppercase tracking-widest flex justify-between border-b-4 border-slate-900">
                            <span>Деталь</span>
                            <span>К-сть / Ціна / Вага</span>
                          </div>
                          <ul className="divide-y-2 divide-slate-200">
                            {aggregateComponents(entry.result.selected).map((comp) => (
                              <li key={comp.id} className="px-4 py-3 flex justify-between items-center hover:bg-slate-100 transition-colors">
                                <div>
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-black uppercase tracking-tight text-slate-900">{comp.name}</span>
                                    {/* Кількость */}
                                    {(comp.quantity || 1) > 1 && (
                                      <span className="bg-red-500 text-white border-2 border-slate-900 text-[10px] font-black px-2 py-0.5 rounded-lg shadow-[2px_2px_0px_0px_#0f172a]">
                                        ×{comp.quantity}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{comp.category}</p>
                                </div>
                                <div className="text-right text-xs font-black uppercase tracking-wider text-slate-900">
                                  <p>
                                    {comp.price * (comp.quantity || 1)} ₴ 
                                    {(comp.quantity || 1) > 1 && <span className="text-slate-400 font-bold ml-1">({comp.price} шт)</span>}
                                  </p>
                                  <p className="text-slate-500 font-bold">
                                    {Number((comp.weight * (comp.quantity || 1)).toFixed(1))} г
                                  </p>
                                </div>
                              </li>
                            ))}
                          </ul>
                          <div className="px-4 py-4 bg-[#facc15] border-t-4 border-slate-900 flex justify-between items-center font-black uppercase tracking-widest text-sm text-slate-900">
                            <span>Всього</span>
                            <div className="text-right flex items-center gap-4">
                              <span className="bg-green-500 text-white px-2 py-1 rounded border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">{entry.result.total_price} ₴</span>
                              <span className="bg-white text-slate-900 px-2 py-1 rounded border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">{entry.result.total_weight} г</span>
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

      {/* КАСТОМНЕ МОДАЛЬНЕ ВІКНО */}
      <AnimatePresence>
        {showConfirmModal && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm px-4"
          >
            <motion.div 
              initial={{ scale: 0.95, y: 20, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="bg-white rounded-2xl border-4 border-slate-900 shadow-[12px_12px_0px_0px_#0f172a] p-8 max-w-sm w-full text-center"
            >
              <div className="mx-auto w-20 h-20 bg-red-500 border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] text-white rounded-full flex items-center justify-center mb-6 text-3xl">
                <FaTrash />
              </div>
              <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900 mb-2">Очистити історію?</h3>
              <p className="text-slate-600 font-bold mb-8">
                Ви впевнені? Цю дію неможливо скасувати.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 py-3 bg-white border-4 border-slate-900 text-slate-900 font-black uppercase tracking-widest rounded-xl hover:bg-slate-100 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 hover:shadow-[0px_0px_0px_0px_#0f172a] transition-all"
                >
                  Ні
                </button>
                <button
                  onClick={performClearHistory}
                  className="flex-1 py-3 bg-red-500 border-4 border-slate-900 text-white font-black uppercase tracking-widest rounded-xl hover:bg-red-600 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 hover:shadow-[0px_0px_0px_0px_#0f172a] transition-all"
                >
                  Так
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
  <div className="flex items-center gap-3 bg-white p-3 rounded-xl border-4 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]">
    <div className={`p-3 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-slate-900 ${color}`}>{icon}</div>
    <div>
      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{label}</p>
      <p className={`text-sm font-black text-slate-900 ${capitalize ? "uppercase" : ""}`}>{value}</p>
    </div>
  </div>
);