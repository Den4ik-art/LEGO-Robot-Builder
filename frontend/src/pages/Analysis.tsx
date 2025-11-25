import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  FaChartLine, FaServer, FaDatabase, FaMicrochip, 
  FaPlay, FaCheckCircle, FaExclamationTriangle, FaCopy, FaChevronDown, FaChevronUp
} from "react-icons/fa";

type BenchmarkResult = {
  n: number;
  generation_time_ms: number;
  algorithm_time_ms: number;
  total_items_processed: number;
  success: boolean;
  items_selected: number;
};

type ConfigRequestPreview = {
  functions: string[];
  subFunctions: Record<string, string>;
  budget: number;
  weight: number;
  priority: string;
  sensors: string[];
};

const DEFAULT_CONFIG: ConfigRequestPreview = {
  functions: ["їздити", "літати", "сканувати"],
  subFunctions: { "їздити": "колеса", "літати": "квадрокоптер" },
  budget: 100000,
  weight: 50000,
  priority: "speed",
  sensors: ["Сенсор відстані (УЗ)", "Гіроскоп", "Камера"]
};

export default function Analysis() {
  const [nValue, setNValue] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BenchmarkResult | null>(null);
  const [history, setHistory] = useState<BenchmarkResult[]>([]);
  const [configCollapsed, setConfigCollapsed] = useState(false);
  const [showJSON, setShowJSON] = useState(false);

  const runBenchmark = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/benchmark/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n: nValue }),
      });
      
      if (!res.ok) throw new Error("Помилка сервера");
      
      const data = await res.json();
      setResults(data);
      setHistory(prev => [data, ...prev]);
    } catch (err) {
      alert("Не вдалося запустити тест");
    } finally {
      setLoading(false);
    }
  };

  const copyConfigToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(DEFAULT_CONFIG, null, 2));
      alert("Конфігурацію скопійовано в буфер обміну");
    } catch {
      alert("Не вдалося скопіювати конфігурацію");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 font-sans text-slate-800">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-slate-900 mb-4 flex justify-center items-center gap-3">
            <FaChartLine className="text-blue-600" /> Аналіз Алгоритму
          </h1>
          <p className="text-slate-500 max-w-2xl mx-auto">
            Експериментальна перевірка швидкодії жадібного алгоритму на синтетичних наборах даних.
            Перевірка гіпотези складності <span className="font-mono bg-slate-200 px-1 rounded">O(N log N)</span>.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          
          {/* ЛІВА КОЛОНКА: ПАРАМЕТРИ */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 sticky top-6">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <FaDatabase className="text-slate-400" /> Параметри тесту
              </h2>
              
              <div className="mb-6">
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  Розмір бази (N)
                </label>
                <input 
                  type="number" 
                  value={nValue}
                  onChange={(e) => setNValue(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-xl px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-lg"
                />
                <div className="flex flex-wrap gap-2 mt-3">
                  {[100, 1000, 5000, 10000, 50000, 100000, 200000, 300000, 500000].map(val => (
                    <button 
                      key={val}
                      onClick={() => setNValue(val)}
                      className="text-xs bg-slate-100 hover:bg-slate-200 px-2 py-1 rounded transition"
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={runBenchmark}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {loading ? (
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                ) : (
                  <><FaPlay /> Запустити Тест</>
                )}
              </button>
            </div>
          </div>

          {/* ПРАВА КОЛОНКА: РЕЗУЛЬТАТИ */}
          <div className="md:col-span-2 space-y-6">
            
            {/* Головний результат */}
            {results && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-3xl shadow-xl border border-blue-100 overflow-hidden"
              >
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                  <h3 className="text-2xl font-bold flex items-center gap-2">
                    <FaMicrochip /> Результат для N = {results.n}
                  </h3>
                </div>
                <div className="p-8 grid grid-cols-2 gap-8">
                  <div>
                    <p className="text-sm text-slate-400 uppercase font-bold tracking-wide mb-1">Час алгоритму</p>
                    <p className="text-4xl font-black text-blue-600">
                      {results.algorithm_time_ms.toFixed(2)} <span className="text-lg text-slate-500">мс</span>
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 uppercase font-bold tracking-wide mb-1">Генерація даних</p>
                    <p className="text-4xl font-black text-slate-700">
                      {results.generation_time_ms.toFixed(2)} <span className="text-lg text-slate-500">мс</span>
                    </p>
                  </div>
                  <div className="col-span-2 border-t pt-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      Статус: 
                      {results.success ? (
                        <span className="text-green-600 flex items-center gap-1"><FaCheckCircle /> Успішно</span>
                      ) : (
                        <span className="text-red-600 flex items-center gap-1"><FaExclamationTriangle /> Помилка</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500">
                      Підібрано деталей: <b>{results.items_selected}</b> • Оброблено: <b>{results.total_items_processed}</b>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Конфігурація запиту — Набір характеристик */}
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                <h3 className="font-bold text-slate-700 flex items-center gap-2">
                  <FaServer /> Набір характеристик робота (ConfigRequest)
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => { setConfigCollapsed(prev => !prev); setShowJSON(false); }}
                    className="inline-flex items-center gap-2 text-sm px-3 py-1 rounded hover:bg-slate-100 transition"
                  >
                    {configCollapsed ? <><FaChevronDown /> Розгорнути</> : <><FaChevronUp /> Згорнути</>}
                  </button>
                  <button
                    onClick={copyConfigToClipboard}
                    className="inline-flex items-center gap-2 text-sm px-3 py-1 rounded hover:bg-slate-100 transition"
                    title="Скопіювати JSON конфігурації"
                  >
                    <FaCopy /> Копіювати
                  </button>
                </div>
              </div>

              {!configCollapsed && (
                <div className="p-6 grid md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs uppercase text-slate-400 font-semibold mb-2">Функції</p>
                    <ul className="list-inside list-disc text-sm text-slate-700 mb-4">
                      {DEFAULT_CONFIG.functions.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>

                    <p className="text-xs uppercase text-slate-400 font-semibold mb-2">Під-функції</p>
                    <div className="text-sm text-slate-700 mb-4">
                      {Object.entries(DEFAULT_CONFIG.subFunctions).map(([k,v]) => (
                        <div key={k} className="flex justify-between py-1 border-b last:border-b-0">
                          <span className="font-medium">{k}</span>
                          <span className="text-slate-500">{v}</span>
                        </div>
                      ))}
                    </div>

                    <p className="text-xs uppercase text-slate-400 font-semibold mb-2">Датчики</p>
                    <ul className="list-inside list-disc text-sm text-slate-700">
                      {DEFAULT_CONFIG.sensors.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs uppercase text-slate-400 font-semibold mb-2">Обмеження / пріоритет</p>
                    <div className="text-sm text-slate-700 mb-4">
                      <div className="flex justify-between py-1"><span className="font-medium">Бюджет</span><span className="font-mono">{DEFAULT_CONFIG.budget}</span></div>
                      <div className="flex justify-between py-1"><span className="font-medium">Вага</span><span className="font-mono">{DEFAULT_CONFIG.weight}</span></div>
                      <div className="flex justify-between py-1"><span className="font-medium">Пріоритет</span><span className="font-mono">{DEFAULT_CONFIG.priority}</span></div>
                    </div>

                    <div className="mt-4">
                      <button
                        onClick={() => setShowJSON(prev => !prev)}
                        className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 transition text-sm"
                      >
                        {showJSON ? "Сховати JSON" : "Показати JSON"}
                      </button>
                    </div>

                    {showJSON && (
                      <pre className="mt-4 bg-slate-50 p-3 rounded text-xs overflow-auto border border-slate-100 font-mono">
                        {JSON.stringify(DEFAULT_CONFIG, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Історія тестів (Таблиця) */}
            {history.length > 0 && (
              <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                  <h3 className="font-bold text-slate-700">Історія запусків</h3>
                </div>
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 uppercase bg-slate-50">
                    <tr>
                      <th className="px-6 py-3">N (Кількість)</th>
                      <th className="px-6 py-3">Алгоритм (мс)</th>
                      <th className="px-6 py-3">Генерація (мс)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h, i) => (
                      <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition">
                        <td className="px-6 py-4 font-medium text-slate-900">{h.n}</td>
                        <td className="px-6 py-4 font-bold text-blue-600">{h.algorithm_time_ms.toFixed(2)}</td>
                        <td className="px-6 py-4 text-slate-500">{h.generation_time_ms.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
