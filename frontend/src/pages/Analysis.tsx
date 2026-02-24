import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaChartLine, FaDatabase, FaMicrochip,
  FaPlay, FaCheckCircle, FaExclamationTriangle, FaCopy, FaChevronDown, FaChevronUp,
  FaDna, FaCogs, FaLeaf, FaBolt
} from "react-icons/fa";

// ═══════════════════════════════════════════════════════
//  TYPES
// ═══════════════════════════════════════════════════════

type AlgoResult = {
  avg_time_ms: number;
  min_time_ms: number;
  max_time_ms: number;
  std_dev_ms: number;
  success_rate: number;
  avg_fitness?: number;
  population_size?: number;
  generations?: number;
};

type ExperimentResult = {
  n: number;
  runs: number;
  dataset_generation_ms: number;
  greedy: AlgoResult;
  genetic?: AlgoResult;
  theoretical_n_log_n?: number;
  greedy_coefficient?: number;
};

type FullComparisonResult = {
  experiments: ExperimentResult[];
  summary: {
    total_experiments: number;
    total_time_ms: number;
    n_values: number[];
    runs_per_n: number;
    eco_mode: boolean;
    greedy_complexity_analysis?: {
      coefficients: number[];
      coefficient_range: number;
      is_approximately_n_log_n: boolean;
    };
    ga_vs_greedy_speed_ratio?: {
      avg_ratio: number;
      description: string;
    };
  };
};

type OldBenchmarkResult = {
  n: number;
  generation_time_ms: number;
  algorithm_time_ms: number;
  total_items_processed: number;
  success: boolean;
  items_selected: number;
};

// ═══════════════════════════════════════════════════════
//  COMPONENT
// ═══════════════════════════════════════════════════════

export default function Analysis() {
  // Mode: "comparison" (new full analytics) or "single" (old benchmark)
  const [mode, setMode] = useState<"comparison" | "single">("comparison");

  // --- Single Mode State (old benchmark) ---
  const [nValue, setNValue] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [singleResult, setSingleResult] = useState<OldBenchmarkResult | null>(null);
  const [singleHistory, setSingleHistory] = useState<OldBenchmarkResult[]>([]);

  // --- Comparison Mode State ---
  const [compNValues, setCompNValues] = useState("100,500,1000,5000,10000");
  const [runsPerN, setRunsPerN] = useState(5);
  const [runGa, setRunGa] = useState(true);
  const [ecoMode, setEcoMode] = useState(false);
  const [gaPopulation, setGaPopulation] = useState(30);
  const [gaGenerations, setGaGenerations] = useState(20);
  const [compResult, setCompResult] = useState<FullComparisonResult | null>(null);
  const [compLoading, setCompLoading] = useState(false);

  const [configCollapsed, setConfigCollapsed] = useState(false);

  // --- Run Old Benchmark ---
  const runSingleBenchmark = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/benchmark/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n: nValue }),
      });
      if (!res.ok) throw new Error("Помилка сервера");
      const data = await res.json();
      setSingleResult(data);
      setSingleHistory(prev => [data, ...prev]);
    } catch {
      alert("Не вдалося запустити тест");
    } finally {
      setLoading(false);
    }
  };

  // --- Run Full Comparison ---
  const runComparison = async () => {
    setCompLoading(true);
    try {
      const nVals = compNValues.split(",").map(s => parseInt(s.trim())).filter(n => n > 0);
      const res = await fetch("http://127.0.0.1:8000/analytics/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          n_values: nVals,
          runs_per_n: runsPerN,
          run_ga: runGa,
          eco_mode: ecoMode,
          ga_population: gaPopulation,
          ga_generations: gaGenerations,
        }),
      });
      if (!res.ok) throw new Error("Помилка сервера");
      const data: FullComparisonResult = await res.json();
      setCompResult(data);
    } catch {
      alert("Не вдалося запустити порівняльний аналіз");
    } finally {
      setCompLoading(false);
    }
  };

  const copyResultToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(compResult, null, 2));
      alert("Результати скопійовано в буфер обміну");
    } catch {
      alert("Не вдалося скопіювати");
    }
  };

  // Max bar height for chart
  const maxGreedyTime = compResult
    ? Math.max(...compResult.experiments.map(e => e.greedy.avg_time_ms), 1)
    : 1;
  const maxGaTime = compResult && runGa
    ? Math.max(...compResult.experiments.filter(e => e.genetic).map(e => e.genetic!.avg_time_ms), 1)
    : 1;
  const maxTime = Math.max(maxGreedyTime, maxGaTime);

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 font-sans text-slate-800">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-extrabold text-slate-900 mb-3 flex justify-center items-center gap-3">
            <FaChartLine className="text-blue-600" /> Аналіз Алгоритмів
          </h1>
          <p className="text-slate-500 max-w-3xl mx-auto">
            Порівняльний аналіз продуктивності <b>Greedy</b> vs <b>Genetic Algorithm</b>.
            Вимірювання T(N) для різних розмірів набору компонентів. Перевірка складності <code className="bg-slate-200 px-1 rounded">O(N log N)</code>.
          </p>
        </div>

        {/* Mode Tabs */}
        <div className="flex justify-center gap-3 mb-8">
          <button
            onClick={() => setMode("comparison")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all border-2 ${mode === "comparison"
                ? "border-blue-500 bg-blue-50 text-blue-700 shadow-md"
                : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}
          >
            <FaDna /> Порівняльний аналіз
          </button>
          <button
            onClick={() => setMode("single")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all border-2 ${mode === "single"
                ? "border-blue-500 bg-blue-50 text-blue-700 shadow-md"
                : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}
          >
            <FaCogs /> Однократний тест
          </button>
        </div>

        {/* ═══════════════════════════════════════════════ */}
        {/* COMPARISON MODE */}
        {/* ═══════════════════════════════════════════════ */}
        {mode === "comparison" && (
          <div className="grid md:grid-cols-3 gap-8">
            {/* Left: Parameters */}
            <div className="md:col-span-1">
              <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 sticky top-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <FaDatabase className="text-slate-400" /> Параметри
                </h2>

                {/* N Values */}
                <div className="mb-4">
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Розміри N (через кому)
                  </label>
                  <input
                    type="text"
                    value={compNValues}
                    onChange={(e) => setCompNValues(e.target.value)}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {["100,500,1000,5000", "100,500,1000,5000,10000", "100,1000,10000,50000", "1000,5000,10000,50000,100000"].map(preset => (
                      <button
                        key={preset}
                        onClick={() => setCompNValues(preset)}
                        className="text-[10px] bg-slate-100 hover:bg-slate-200 px-2 py-1 rounded transition"
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Runs per N */}
                <div className="mb-4">
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Повторень (R)
                  </label>
                  <input
                    type="number"
                    value={runsPerN}
                    onChange={(e) => setRunsPerN(Number(e.target.value))}
                    min={1}
                    max={20}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs font-mono focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                {/* Toggles */}
                <div className="space-y-3 mb-4">
                  <ToggleSwitch
                    label="Генетичний алгоритм"
                    description="Включити GA у порівняння"
                    icon={<FaDna className="text-emerald-500" />}
                    active={runGa}
                    onToggle={() => setRunGa(!runGa)}
                  />
                  <ToggleSwitch
                    label="Eco-Mode"
                    description="Мінімізація енергоспоживання"
                    icon={<FaLeaf className="text-emerald-500" />}
                    active={ecoMode}
                    onToggle={() => setEcoMode(!ecoMode)}
                  />
                </div>

                {/* GA Parameters */}
                <AnimatePresence>
                  {runGa && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden mb-4"
                    >
                      <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 space-y-2">
                        <p className="text-[10px] font-bold text-emerald-700 uppercase">GA Параметри</p>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="text-[10px] text-emerald-600">Популяція</label>
                            <input
                              type="number"
                              value={gaPopulation}
                              onChange={(e) => setGaPopulation(Number(e.target.value))}
                              className="w-full border border-emerald-200 rounded-lg px-2 py-1 text-xs font-mono"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-emerald-600">Покоління</label>
                            <input
                              type="number"
                              value={gaGenerations}
                              onChange={(e) => setGaGenerations(Number(e.target.value))}
                              className="w-full border border-emerald-200 rounded-lg px-2 py-1 text-xs font-mono"
                            />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Run Button */}
                <button
                  onClick={runComparison}
                  disabled={compLoading}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                >
                  {compLoading ? (
                    <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                  ) : (
                    <><FaPlay /> Запустити аналіз</>
                  )}
                </button>
              </div>
            </div>

            {/* Right: Results */}
            <div className="md:col-span-2 space-y-6">
              {compResult && (
                <>
                  {/* Summary Card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-3xl shadow-xl border border-blue-100 overflow-hidden"
                  >
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white flex items-center justify-between">
                      <div>
                        <h3 className="text-2xl font-bold flex items-center gap-2">
                          <FaMicrochip /> Результати аналізу
                        </h3>
                        <p className="text-blue-200 text-sm mt-1">
                          {compResult.summary.total_experiments} &times; {compResult.summary.runs_per_n}R
                          {compResult.summary.eco_mode && " | Eco-Mode"}
                          {" | "}{(compResult.summary.total_time_ms / 1000).toFixed(1)}s
                        </p>
                      </div>
                      <button
                        onClick={copyResultToClipboard}
                        className="text-blue-200 hover:text-white transition"
                        title="Копіювати JSON"
                      >
                        <FaCopy className="text-lg" />
                      </button>
                    </div>

                    {/* Summary Grid */}
                    <div className="p-6 grid grid-cols-2 md:grid-cols-3 gap-4">
                      {/* Complexity Analysis */}
                      {compResult.summary.greedy_complexity_analysis && (
                        <div className="col-span-2 md:col-span-3 p-4 bg-slate-50 rounded-2xl border border-slate-200">
                          <h4 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-2">
                            <FaBolt className="text-amber-500" /> Аналіз складності O(N log N)
                          </h4>
                          <div className="flex items-center gap-3">
                            {compResult.summary.greedy_complexity_analysis.is_approximately_n_log_n ? (
                              <span className="text-green-600 flex items-center gap-1 text-sm font-semibold">
                                <FaCheckCircle /> Підтверджено
                              </span>
                            ) : (
                              <span className="text-amber-600 flex items-center gap-1 text-sm font-semibold">
                                <FaExclamationTriangle /> Потребує додаткового аналізу
                              </span>
                            )}
                            <span className="text-xs text-slate-500">
                              Діапазон коефіцієнтів: {compResult.summary.greedy_complexity_analysis.coefficient_range}x
                            </span>
                          </div>
                        </div>
                      )}

                      {/* GA vs Greedy Ratio */}
                      {compResult.summary.ga_vs_greedy_speed_ratio && (
                        <div className="col-span-2 md:col-span-3 p-4 bg-emerald-50 rounded-2xl border border-emerald-200">
                          <h4 className="text-xs font-bold text-emerald-700 mb-1 flex items-center gap-2">
                            <FaDna className="text-emerald-500" /> Співвідношення Greedy / GA
                          </h4>
                          <p className="text-sm text-emerald-800">
                            {compResult.summary.ga_vs_greedy_speed_ratio.description}
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>

                  {/* Bar Chart */}
                  <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-6">
                    <h3 className="font-bold text-slate-700 mb-4">T(N) — Час виконання (мс)</h3>
                    <div className="flex items-end gap-2 h-64 border-b border-l border-slate-200 p-4 pt-0 relative">
                      {compResult.experiments.map((exp, i) => {
                        const greedyH = (exp.greedy.avg_time_ms / maxTime) * 100;
                        const gaH = exp.genetic ? (exp.genetic.avg_time_ms / maxTime) * 100 : 0;
                        return (
                          <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                            <div className="flex items-end gap-0.5 h-full w-full justify-center">
                              {/* Greedy bar */}
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: `${Math.max(greedyH, 2)}%` }}
                                transition={{ delay: i * 0.1, duration: 0.5 }}
                                className="w-5 bg-blue-500 rounded-t-lg relative group"
                              >
                                <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[9px] font-bold text-blue-700 whitespace-nowrap opacity-0 group-hover:opacity-100 transition">
                                  {exp.greedy.avg_time_ms.toFixed(1)}ms
                                </div>
                              </motion.div>
                              {/* GA bar */}
                              {exp.genetic && (
                                <motion.div
                                  initial={{ height: 0 }}
                                  animate={{ height: `${Math.max(gaH, 2)}%` }}
                                  transition={{ delay: i * 0.1 + 0.05, duration: 0.5 }}
                                  className="w-5 bg-emerald-500 rounded-t-lg relative group"
                                >
                                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[9px] font-bold text-emerald-700 whitespace-nowrap opacity-0 group-hover:opacity-100 transition">
                                    {exp.genetic.avg_time_ms.toFixed(1)}ms
                                  </div>
                                </motion.div>
                              )}
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono mt-1">
                              {exp.n >= 1000 ? `${exp.n / 1000}K` : exp.n}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                    <div className="flex justify-center gap-6 mt-3 text-xs">
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 bg-blue-500 rounded" /> Greedy
                      </span>
                      {runGa && (
                        <span className="flex items-center gap-1.5">
                          <span className="w-3 h-3 bg-emerald-500 rounded" /> Genetic
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Data Table */}
                  <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                      <h3 className="font-bold text-slate-700">Деталізовані результати</h3>
                      <button
                        onClick={() => setConfigCollapsed(prev => !prev)}
                        className="text-sm text-slate-500 hover:text-slate-700 transition"
                      >
                        {configCollapsed ? <FaChevronDown /> : <FaChevronUp />}
                      </button>
                    </div>
                    {!configCollapsed && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left">
                          <thead className="text-[10px] text-slate-500 uppercase bg-slate-50">
                            <tr>
                              <th className="px-4 py-2.5">N</th>
                              <th className="px-4 py-2.5">Greedy avg (мс)</th>
                              <th className="px-4 py-2.5">Greedy std</th>
                              <th className="px-4 py-2.5">Success</th>
                              {runGa && <>
                                <th className="px-4 py-2.5">GA avg (мс)</th>
                                <th className="px-4 py-2.5">GA std</th>
                                <th className="px-4 py-2.5">Fitness</th>
                              </>}
                              <th className="px-4 py-2.5">N·log₂N</th>
                              <th className="px-4 py-2.5">Coeff</th>
                            </tr>
                          </thead>
                          <tbody>
                            {compResult.experiments.map((exp, i) => (
                              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition">
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">{exp.n.toLocaleString()}</td>
                                <td className="px-4 py-3 font-bold text-blue-600">{exp.greedy.avg_time_ms.toFixed(2)}</td>
                                <td className="px-4 py-3 text-slate-500">±{exp.greedy.std_dev_ms.toFixed(2)}</td>
                                <td className="px-4 py-3">
                                  {exp.greedy.success_rate === 1 ? (
                                    <FaCheckCircle className="text-green-500" />
                                  ) : (
                                    <span className="text-amber-500">{(exp.greedy.success_rate * 100).toFixed(0)}%</span>
                                  )}
                                </td>
                                {runGa && exp.genetic && <>
                                  <td className="px-4 py-3 font-bold text-emerald-600">{exp.genetic.avg_time_ms.toFixed(2)}</td>
                                  <td className="px-4 py-3 text-slate-500">±{exp.genetic.std_dev_ms.toFixed(2)}</td>
                                  <td className="px-4 py-3 text-slate-700">{exp.genetic.avg_fitness?.toFixed(2)}</td>
                                </>}
                                {runGa && !exp.genetic && <>
                                  <td className="px-4 py-3 text-slate-300">—</td>
                                  <td className="px-4 py-3 text-slate-300">—</td>
                                  <td className="px-4 py-3 text-slate-300">—</td>
                                </>}
                                <td className="px-4 py-3 text-slate-500 font-mono">{exp.theoretical_n_log_n?.toFixed(0)}</td>
                                <td className="px-4 py-3 text-slate-500 font-mono">{exp.greedy_coefficient?.toFixed(4)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              )}

              {!compResult && !compLoading && (
                <div className="border border-dashed border-slate-200 rounded-3xl p-16 text-center text-slate-400">
                  <FaChartLine className="text-4xl mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Налаштуйте параметри та натисніть «Запустити аналіз»</p>
                </div>
              )}

              {compLoading && (
                <div className="border border-dashed border-blue-200 rounded-3xl p-16 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-sm text-blue-600 font-medium">Виконуються експерименти...</p>
                  <p className="text-xs text-slate-400 mt-1">Це може зайняти кілька хвилин</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════ */}
        {/* SINGLE TEST MODE (old benchmark) */}
        {/* ═══════════════════════════════════════════════ */}
        {mode === "single" && (
          <div className="grid md:grid-cols-3 gap-8">
            <div className="md:col-span-1">
              <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 sticky top-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <FaDatabase className="text-slate-400" /> Однократний тест
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
                        {val.toLocaleString()}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={runSingleBenchmark}
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

            <div className="md:col-span-2 space-y-6">
              {singleResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-3xl shadow-xl border border-blue-100 overflow-hidden"
                >
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                    <h3 className="text-2xl font-bold flex items-center gap-2">
                      <FaMicrochip /> Результат для N = {singleResult.n.toLocaleString()}
                    </h3>
                  </div>
                  <div className="p-8 grid grid-cols-2 gap-8">
                    <div>
                      <p className="text-sm text-slate-400 uppercase font-bold tracking-wide mb-1">Час алгоритму</p>
                      <p className="text-4xl font-black text-blue-600">
                        {singleResult.algorithm_time_ms.toFixed(2)} <span className="text-lg text-slate-500">мс</span>
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 uppercase font-bold tracking-wide mb-1">Генерація даних</p>
                      <p className="text-4xl font-black text-slate-700">
                        {singleResult.generation_time_ms.toFixed(2)} <span className="text-lg text-slate-500">мс</span>
                      </p>
                    </div>
                    <div className="col-span-2 border-t pt-4 flex justify-between items-center">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        Статус:
                        {singleResult.success ? (
                          <span className="text-green-600 flex items-center gap-1"><FaCheckCircle /> Успішно</span>
                        ) : (
                          <span className="text-red-600 flex items-center gap-1"><FaExclamationTriangle /> Помилка</span>
                        )}
                      </div>
                      <div className="text-sm text-slate-500">
                        Підібрано деталей: <b>{singleResult.items_selected}</b> • Оброблено: <b>{singleResult.total_items_processed.toLocaleString()}</b>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {singleHistory.length > 0 && (
                <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="font-bold text-slate-700">Історія запусків</h3>
                  </div>
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-50">
                      <tr>
                        <th className="px-6 py-3">N</th>
                        <th className="px-6 py-3">Алгоритм (мс)</th>
                        <th className="px-6 py-3">Генерація (мс)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {singleHistory.map((h, i) => (
                        <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition">
                          <td className="px-6 py-4 font-medium text-slate-900">{h.n.toLocaleString()}</td>
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
        )}

      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
//  HELPER COMPONENTS
// ═══════════════════════════════════════════════════════

const ToggleSwitch: React.FC<{
  label: string;
  description: string;
  icon: React.ReactNode;
  active: boolean;
  onToggle: () => void;
}> = ({ label, description, icon, active, onToggle }) => (
  <button
    type="button"
    onClick={onToggle}
    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all border ${active
        ? "border-emerald-400 bg-emerald-50 text-emerald-700"
        : "border-slate-200 bg-slate-50 text-slate-500 hover:border-slate-300"
      }`}
  >
    <span className="flex items-center gap-2">
      {icon}
      <div className="text-left">
        <div className="font-semibold">{label}</div>
        <div className="text-[10px] opacity-60">{description}</div>
      </div>
    </span>
    <div className={`w-9 h-5 rounded-full relative transition-colors ${active ? "bg-emerald-500" : "bg-slate-300"
      }`}>
      <div className={`w-3.5 h-3.5 bg-white rounded-full absolute top-[3px] transition-all shadow ${active ? "left-[18px]" : "left-[3px]"
        }`} />
    </div>
  </button>
);
