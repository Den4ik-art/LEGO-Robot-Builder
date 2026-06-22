import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Line, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer,
  BarChart, Bar, Cell, ComposedChart, Area, ScatterChart, Scatter, ZAxis,
  Tooltip as RechartsTooltip, ErrorBar, AreaChart
} from "recharts";
import {
  Gauge, Cpu, FlaskConical, Binary, Play, Settings2, BarChart2,
  Activity, ArrowRight, Lightbulb, TrendingUp, DollarSign, BrainCircuit,
  AlertTriangle, Hammer, Cog
} from "lucide-react";

// ═══════════════════════════════════════════════════════
// UI COMPONENTS
// ═══════════════════════════════════════════════════════

const ChartCard = ({ title, children, icon, className = "" }: any) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`bg-white border-4 border-slate-900 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-5 flex flex-col ${className}`}
  >
    <div className="flex items-center gap-2 mb-4 pb-2 border-b-4 border-slate-900">
      <div className="p-2 bg-yellow-400 border-2 border-slate-900 rounded-sm">
        {icon}
      </div>
      <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">{title}</h3>
    </div>
    <div className="flex-1 min-h-0 w-full relative">
      {children}
    </div>
  </motion.div>
);

const HighlightCard = ({ title, value, subtitle, icon, color = "bg-emerald-400" }: any) => (
  <motion.div
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
    className={`border-4 border-slate-900 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] p-4 flex items-center gap-4 ${color}`}
  >
    <div className="p-3 bg-white border-2 border-slate-900 rounded-full flex-shrink-0">
      {icon}
    </div>
    <div>
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">{title}</h4>
      <div className="text-2xl font-black text-slate-900">{value}</div>
      {subtitle && <div className="text-sm font-bold text-slate-700">{subtitle}</div>}
    </div>
  </motion.div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border-2 border-emerald-400 p-3 shadow-[4px_4px_0px_0px_rgba(16,185,129,1)]">
        <p className="font-bold text-white mb-2">{label || "Деталі"}</p>
        {payload.map((entry: any, index: any) => {
          let deltaText = "";
          if (entry.payload && entry.payload.delta && entry.dataKey === entry.payload.targetKey) {
             deltaText = ` (${entry.payload.delta > 0 ? '+' : ''}${entry.payload.delta.toFixed(1)}%)`;
          }
          return (
            <p key={`item-${index}`} style={{ color: entry.color }} className="font-mono text-sm">
              <span className="font-bold">{entry.name}:</span> {Number(entry.value).toFixed(2)}{deltaText}
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

// ═══════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ═══════════════════════════════════════════════════════

export default function Analysis() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const [n, setN] = useState(1000);
  const [runGreedy, setRunGreedy] = useState(true);
  const [runGenetic, setRunGenetic] = useState(true);
  const [ecoMode, setEcoMode] = useState(false);
  const [gaPop, setGaPop] = useState(50);
  const [gaGen, setGaGen] = useState(30);

  const colors = { "Жадібний": "#facc15", "Генетичний": "#10b981", Base: "#3b82f6" };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await axios.post("http://127.0.0.1:8000/analytics/dashboard", {
        n,
        run_greedy: runGreedy,
        run_genetic: runGenetic,
        eco_mode: ecoMode,
        ga_population: gaPop,
        ga_generations: gaGen
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setError("Помилка при запуску аналізу. Перевірте підключення до бекенду.");
    } finally {
      setLoading(false);
    }
  };

  // ── DATA PREPARATION ──

  const getRadarData = () => {
    if (!result) return [];
    const axes = { speed: "ШВИДКІСТЬ", force: "СИЛА", economy: "ЕКОНОМІЯ", endurance: "ВИТРИВАЛІСТЬ", eco: "ЕКО" };
    return Object.keys(axes).map(axis => {
      const dataPoint: any = { subject: axes[axis as keyof typeof axes] };
      if (result.algorithms.Greedy?.characteristics) {
        dataPoint["Жадібний"] = result.algorithms.Greedy.characteristics[axis] || 0;
      }
      if (result.algorithms.Genetic?.characteristics) {
        dataPoint["Генетичний"] = result.algorithms.Genetic.characteristics[axis] || 0;
      }
      return dataPoint;
    });
  };

  const getEfficiencyData = () => {
    if (!result) return [];
    return Object.values(result.algorithms).map((a: any) => ({
      name: a.name === "Greedy" ? "Жадібний" : "Генетичний",
      "Продуктивність (Якість/Час)": a.time_ms > 0 ? Number((a.fitness / a.time_ms * 10).toFixed(2)) : 0,
      "Економічна вигода (Якість/1k₴)": a.total_price > 0 ? Number((a.fitness / (a.total_price / 1000)).toFixed(2)) : 0,
    }));
  };

  const getScatterData = () => {
    if (!result) return [];
    return Object.values(result.algorithms).map((a: any) => ({
      name: a.name === "Greedy" ? "Жадібний" : "Генетичний",
      time: a.time_ms,
      fitness: a.fitness,
      parts: a.parts_count,
    }));
  };

  const getSpeedData = () => {
    if (!result) return [];
    return Object.values(result.algorithms).map((a: any) => ({
      name: a.name === "Greedy" ? "Жадібний" : "Генетичний",
      "Час (мс)": a.time_ms,
    }));
  };

  const getCategoryBreakdownData = () => {
    if (!result) return [];
    const data = [];
    if (result.algorithms.Greedy?.category_breakdown) {
      const g: any = { name: "Жадібний" };
      Object.assign(g, result.algorithms.Greedy.category_breakdown);
      data.push(g);
    }
    if (result.algorithms.Genetic?.category_breakdown) {
      const ga: any = { name: "Генетичний" };
      Object.assign(ga, result.algorithms.Genetic.category_breakdown);
      data.push(ga);
    }
    return data;
  };

  const getCategoryResourceData = (resourceKey: string) => {
    if (!result) return [];
    const data = [];
    if (result.algorithms.Greedy && result.algorithms.Greedy[resourceKey]) {
      const g: any = { name: "Жадібний" };
      Object.assign(g, result.algorithms.Greedy[resourceKey]);
      data.push(g);
    }
    if (result.algorithms.Genetic && result.algorithms.Genetic[resourceKey]) {
      const ga: any = { name: "Генетичний" };
      Object.assign(ga, result.algorithms.Genetic[resourceKey]);
      data.push(ga);
    }
    return data;
  };

  const categories = Array.from(new Set(
    Object.values(result?.algorithms || {}).flatMap((a: any) => [
      ...Object.keys(a.category_breakdown || {}),
      ...Object.keys(a.category_price || {}),
      ...Object.keys(a.category_weight || {})
    ])
  ));
  const catColors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"];

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans pb-20">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* HEADER */}
        <div className="flex justify-between items-end border-b-8 border-slate-900 pb-4">
          <div>
            <h1 className="text-5xl font-black uppercase tracking-tighter text-slate-900">
              Аналітичний Дашборд
            </h1>
            <p className="text-xl font-bold text-slate-600 mt-2">
              Система Підтримки Прийняття Рішень: Еволюція vs Жадібність
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={loading || (!runGreedy && !runGenetic)}
            className="group relative px-8 py-4 bg-emerald-400 border-4 border-slate-900 font-black text-xl uppercase tracking-wider hover:bg-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <div className="absolute inset-0 bg-slate-900 translate-x-2 translate-y-2 -z-10 group-hover:translate-x-1 group-hover:translate-y-1 transition-transform"></div>
            {loading ? (
              <span className="flex items-center gap-2"><Cog className="animate-spin" /> Обчислення...</span>
            ) : (
              <span className="flex items-center gap-2"><Play /> Запуск Аналізу</span>
            )}
          </button>
        </div>

        {error && (
          <div className="bg-red-400 border-4 border-slate-900 p-4 font-bold text-slate-900 flex items-center gap-3 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <AlertTriangle size={24} /> {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* SIDEBAR (Parameters) */}
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-yellow-100 border-4 border-slate-900 p-5 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
              <h2 className="text-xl font-black uppercase mb-4 flex items-center gap-2 border-b-4 border-slate-900 pb-2">
                <Settings2 /> Параметри
              </h2>
              
              <div className="space-y-4 font-bold text-slate-800">
                <div>
                  <label className="block mb-1 text-sm uppercase">База деталей (N): {n}</label>
                  <input type="range" min="100" max="10000" step="100" value={n} onChange={e => setN(Number(e.target.value))} className="w-full accent-slate-900" />
                </div>
                
                <label className="flex items-center gap-2 cursor-pointer p-2 hover:bg-yellow-200 border-2 border-transparent hover:border-slate-900 transition-colors">
                  <input type="checkbox" checked={runGreedy} onChange={e => setRunGreedy(e.target.checked)} className="w-5 h-5 accent-yellow-500 border-2 border-slate-900" />
                  Жадібний Алгоритм
                </label>
                
                <label className="flex items-center gap-2 cursor-pointer p-2 hover:bg-yellow-200 border-2 border-transparent hover:border-slate-900 transition-colors">
                  <input type="checkbox" checked={runGenetic} onChange={e => setRunGenetic(e.target.checked)} className="w-5 h-5 accent-emerald-500 border-2 border-slate-900" />
                  Генетичний Алгоритм
                </label>

                <AnimatePresence>
                  {runGenetic && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="pl-4 border-l-4 border-emerald-500 space-y-3 overflow-hidden"
                    >
                      <div>
                        <label className="block text-xs uppercase mb-1">Популяція: {gaPop}</label>
                        <input type="range" min="10" max="200" step="10" value={gaPop} onChange={e => setGaPop(Number(e.target.value))} className="w-full accent-emerald-500" />
                      </div>
                      <div>
                        <label className="block text-xs uppercase mb-1">Покоління: {gaGen}</label>
                        <input type="range" min="10" max="100" step="5" value={gaGen} onChange={e => setGaGen(Number(e.target.value))} className="w-full accent-emerald-500" />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <label className="flex items-center gap-2 cursor-pointer p-2 hover:bg-yellow-200 border-2 border-transparent hover:border-slate-900 transition-colors">
                  <input type="checkbox" checked={ecoMode} onChange={e => setEcoMode(e.target.checked)} className="w-5 h-5 accent-blue-500 border-2 border-slate-900" />
                  Eco Mode (Енергозбереження)
                </label>
              </div>
            </div>


          </div>

          {/* MAIN CONTENT AREA */}
          <div className="lg:col-span-9 space-y-6">
            {!result && !loading ? (
              <div className="h-[600px] border-4 border-dashed border-slate-400 flex flex-col items-center justify-center text-slate-400 relative overflow-hidden">
                <Hammer className="w-24 h-24 mb-4 opacity-50" />
                <h2 className="text-2xl font-black uppercase tracking-widest">Очікування даних</h2>
                <p className="font-bold text-sm mt-2">Запустіть аналіз для відображення інженерних метрик</p>
              </div>
            ) : loading ? (
              <div className="h-[600px] border-4 border-slate-900 flex flex-col items-center justify-center bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                <Cog className="w-20 h-20 animate-spin text-emerald-500 mb-6" />
                <h2 className="text-3xl font-black uppercase tracking-widest animate-pulse">Компіляція...</h2>
              </div>
            ) : result ? (
              <div className="space-y-6">
                
                {/* COMPARISON TABLE */}
                <div className="grid grid-cols-1 gap-4">
                  <ChartCard title="Порівняльна Таблиця" icon={<Activity />} className="w-full">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b-4 border-slate-900 bg-slate-100">
                            <th className="p-3 font-black uppercase text-slate-900 border-r-4 border-slate-900">Метрика</th>
                            {result.algorithms.Greedy && <th className="p-3 font-black uppercase text-slate-900 border-r-4 border-slate-900">Жадібний Алгоритм</th>}
                            {result.algorithms.Genetic && <th className="p-3 font-black uppercase text-slate-900">Генетичний Алгоритм</th>}
                          </tr>
                        </thead>
                        <tbody className="font-bold text-slate-800">
                          <tr className="border-b-2 border-slate-200">
                            <td className="p-3 border-r-4 border-slate-900">Оцінка якості (Загальний рейтинг)</td>
                            {result.algorithms.Greedy && <td className="p-3 border-r-4 border-slate-900">{result.algorithms.Greedy.fitness.toFixed(2)}</td>}
                            {result.algorithms.Genetic && <td className="p-3">{result.algorithms.Genetic.fitness.toFixed(2)}</td>}
                          </tr>
                          <tr className="border-b-2 border-slate-200">
                            <td className="p-3 border-r-4 border-slate-900">Час виконання</td>
                            {result.algorithms.Greedy && <td className="p-3 border-r-4 border-slate-900">{result.algorithms.Greedy.time_ms.toFixed(2)} мс</td>}
                            {result.algorithms.Genetic && <td className="p-3">{result.algorithms.Genetic.time_ms.toFixed(2)} мс</td>}
                          </tr>
                          <tr className="border-b-2 border-slate-200">
                            <td className="p-3 border-r-4 border-slate-900">Кількість деталей</td>
                            {result.algorithms.Greedy && <td className="p-3 border-r-4 border-slate-900">{result.algorithms.Greedy.parts_count} шт</td>}
                            {result.algorithms.Genetic && <td className="p-3">{result.algorithms.Genetic.parts_count} шт</td>}
                          </tr>
                          <tr className="border-b-2 border-slate-200">
                            <td className="p-3 border-r-4 border-slate-900">Загальна вартість</td>
                            {result.algorithms.Greedy && <td className="p-3 border-r-4 border-slate-900">{result.algorithms.Greedy.total_price.toFixed(2)} ₴</td>}
                            {result.algorithms.Genetic && <td className="p-3">{result.algorithms.Genetic.total_price.toFixed(2)} ₴</td>}
                          </tr>
                          <tr className="border-b-2 border-slate-200">
                            <td className="p-3 border-r-4 border-slate-900">Загальна вага</td>
                            {result.algorithms.Greedy && <td className="p-3 border-r-4 border-slate-900">{result.algorithms.Greedy.total_weight.toFixed(2)} г</td>}
                            {result.algorithms.Genetic && <td className="p-3">{result.algorithms.Genetic.total_weight.toFixed(2)} г</td>}
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </ChartCard>
                </div>

                {/* HIGHLIGHTS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {result.algorithms.Genetic && (
                    <HighlightCard 
                      title="Найвища якість" 
                      value={result.algorithms.Genetic.fitness.toFixed(2)} 
                      subtitle="Генетичний" 
                      icon={<TrendingUp className="text-emerald-500" />} 
                      color="bg-emerald-300" 
                    />
                  )}
                  {result.algorithms.Greedy && (
                    <HighlightCard 
                      title="Швидкість" 
                      value={`${result.algorithms.Greedy.time_ms.toFixed(0)} мс`} 
                      subtitle="Жадібний" 
                      icon={<Activity className="text-yellow-500" />} 
                      color="bg-yellow-300" 
                    />
                  )}
                  {result.algorithms.Genetic && result.algorithms.Greedy && (
                    <HighlightCard 
                      title="Економічна вигода (Якість/1k₴)" 
                      value={getEfficiencyData().sort((a,b)=>b["Економічна вигода (Якість/1k₴)"]-a["Економічна вигода (Якість/1k₴)"])[0]["Економічна вигода (Якість/1k₴)"].toFixed(2)} 
                      subtitle={getEfficiencyData().sort((a,b)=>b["Економічна вигода (Якість/1k₴)"]-a["Економічна вигода (Якість/1k₴)"])[0].name}
                      icon={<DollarSign className="text-blue-500" />} 
                      color="bg-blue-300" 
                    />
                  )}
                </div>


                {/* CHARTS ROW 1 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
                  {/* RADAR CHART */}
                  <ChartCard title="Радар Характеристик" icon={<Activity />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="70%" data={getRadarData()}>
                        <PolarGrid stroke="#cbd5e1" strokeDasharray="3 3" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#0f172a', fontWeight: 'bold', fontSize: 10 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12, bottom: -10 }} />
                        {result.algorithms.Greedy && (
                          <Radar name="Жадібний" dataKey="Жадібний" stroke={colors["Жадібний"]} fill={colors["Жадібний"]} fillOpacity={0.4} strokeWidth={3} />
                        )}
                        {result.algorithms.Genetic && (
                          <Radar name="Генетичний" dataKey="Генетичний" stroke={colors["Генетичний"]} fill={colors["Генетичний"]} fillOpacity={0.4} strokeWidth={3} />
                        )}
                      </RadarChart>
                    </ResponsiveContainer>
                  </ChartCard>

                  {/* SCATTER CHART */}
                  <ChartCard title="Фронт Ефективності" icon={<FlaskConical />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis type="number" dataKey="time" name="Час (мс)" scale="log" domain={['auto', 'auto']} tick={{ fontWeight: 'bold', fontSize: 12 }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} label={{ value: "Час виконання (лог-шкала)", position: "insideBottom", offset: -15, fontWeight: 'bold', fontSize: 10 }} />
                        <YAxis type="number" dataKey="fitness" name="Фітнес" domain={[0, 100]} tick={{ fontWeight: 'bold', fontSize: 12 }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} label={{ value: "Якість", angle: -90, position: 'insideLeft', fontWeight: 'bold', fontSize: 10 }} />
                        <ZAxis type="number" dataKey="parts" range={[100, 500]} name="Деталей" />
                        <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} content={(props: any) => <CustomTooltip {...props} />} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12, bottom: -15 }} />
                        {getScatterData().map((entry, index) => (
                          <Scatter key={`scatter-${index}`} name={entry.name} data={[entry]} fill={(colors as any)[entry.name]} shape="circle" />
                        ))}
                      </ScatterChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                {/* CHARTS ROW 2 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
                  {/* CATEGORY BREAKDOWN (Resource Heatmap) */}
                  <ChartCard title="Структура Якості" icon={<BarChart2 />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getCategoryBreakdownData()} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis type="number" tick={{ fontWeight: 'bold' }} />
                        <YAxis dataKey="name" type="category" tick={{ fontWeight: 'bold', fontSize: 14 }} width={80} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12 }} />
                        {categories.map((cat, i) => (
                          <Bar key={cat} dataKey={cat} stackId="a" fill={catColors[i % catColors.length]} stroke="#0f172a" strokeWidth={2} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>

                  {/* SPEED CHART */}
                  <ChartCard title="Швидкодія Алгоритмів" icon={<Play />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getSpeedData()} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                        <XAxis type="number" scale="log" domain={['auto', 'auto']} tick={{ fontWeight: 'bold' }} label={{ value: "Час (мс) - лог.шкала", position: "insideBottom", offset: -5, fontSize: 10 }} />
                        <YAxis dataKey="name" type="category" tick={{ fontWeight: 'bold', fontSize: 14 }} width={80} />
                        <RechartsTooltip cursor={{fill: '#f1f5f9'}} content={(props: any) => <CustomTooltip {...props} />} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12 }} />
                        <Bar dataKey="Час (мс)" fill="#f59e0b" stroke="#0f172a" strokeWidth={2}>
                          {getSpeedData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={(colors as any)[entry.name] || "#f59e0b"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                {/* CHARTS ROW 3: RESOURCE BREAKDOWNS */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
                  {/* PRICE BREAKDOWN */}
                  <ChartCard title="Розподіл Бюджету (Ціна)" icon={<DollarSign />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getCategoryResourceData("category_price")} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontWeight: 'bold', fontSize: 14 }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <YAxis tick={{ fontWeight: 'bold' }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} cursor={{fill: '#f1f5f9'}} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12 }} />
                        {categories.map((cat, i) => (
                          <Bar key={cat} dataKey={cat} stackId="a" fill={catColors[i % catColors.length]} stroke="#0f172a" strokeWidth={2} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>

                  {/* WEIGHT BREAKDOWN */}
                  <ChartCard title="Розподіл Маси (Вага)" icon={<Hammer />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getCategoryResourceData("category_weight")} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontWeight: 'bold', fontSize: 14 }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <YAxis tick={{ fontWeight: 'bold' }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} cursor={{fill: '#f1f5f9'}} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12 }} />
                        {categories.map((cat, i) => (
                          <Bar key={cat} dataKey={cat} stackId="a" fill={catColors[i % catColors.length]} stroke="#0f172a" strokeWidth={2} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                {/* CHARTS ROW 4 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
                  {/* VALUE METRICS */}
                  <ChartCard title="Показники Ефективності" icon={<Cpu />} className="h-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getEfficiencyData()} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontWeight: 'bold', fontSize: 14 }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <YAxis tick={{ fontWeight: 'bold' }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} cursor={{fill: '#f1f5f9'}} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12 }} />
                        <Bar dataKey="Продуктивність (Якість/Час)" fill="#6366f1" stroke="#0f172a" strokeWidth={2} />
                        <Bar dataKey="Економічна вигода (Якість/1k₴)" fill="#ec4899" stroke="#0f172a" strokeWidth={2} />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                {/* DEEP DIVE CONVERGENCE (GA ONLY) */}
                {result.algorithms.Genetic && result.algorithms.Genetic.convergence && (
                  <ChartCard title="Конвергенція ГА (Еволюція)" icon={<Binary className="text-emerald-500" />} className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={result.algorithms.Genetic.convergence} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                        <defs>
                          <linearGradient id="colorBest" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="generation" tick={{ fontWeight: 'bold' }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} label={{ value: "Покоління", position: "bottom", offset: 0, fontWeight: 'bold' }} />
                        <YAxis domain={['auto', 'auto']} tick={{ fontWeight: 'bold' }} axisLine={{ strokeWidth: 2, stroke: '#0f172a' }} />
                        <RechartsTooltip content={(props: any) => <CustomTooltip {...props} />} />
                        <Legend wrapperStyle={{ fontWeight: 'bold', fontSize: 12, bottom: 0 }} />
                        <Area type="monotone" name="Найвища якість" dataKey="best_fitness" stroke="#10b981" fillOpacity={1} fill="url(#colorBest)" strokeWidth={3} />
                        <Area type="monotone" name="Середня якість" dataKey="avg_fitness" stroke="#3b82f6" fillOpacity={1} fill="url(#colorAvg)" strokeWidth={2} />
                        <Line type="monotone" name="Різноманітність (StdDev)" dataKey="std_fitness" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </ChartCard>
                )}
                
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
