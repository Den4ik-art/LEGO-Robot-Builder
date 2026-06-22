import React, { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaSearch, FaFilter, FaArrowUp, FaBoxOpen, FaTags, FaLayerGroup } from "react-icons/fa";
import ComponentCard from "../components/ComponentCard";
import type { LegoComponent } from "../types/Component";

const API_URL = "http://127.0.0.1:8000";
const ITEMS_PER_PAGE = 24;

const CATEGORY_TRANSLATIONS: Record<string, string> = {
  all: "Всі категорії",
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

export default function Home() {
  const [components, setComponents] = useState<LegoComponent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Фільтри
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [priceLimit, setPriceLimit] = useState(2000);
  const [maxPrice, setMaxPrice] = useState(2000);
  
  // Пагінація та UI
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);
  const [showScroll, setShowScroll] = useState(false);

  // --- Оптимізація пошуку ---
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // --- Завантаження даних ---
  useEffect(() => {
    const fetchComponents = async () => {
      try {
        const res = await fetch(`${API_URL}/components/`);
        if (!res.ok) throw new Error("Помилка сервера");
        const data = await res.json();
        const list = Array.isArray(data) ? data : [];
        
        setComponents(list);

        if (list.length > 0) {
          const prices = list.map((c: LegoComponent) => c.price);
          const maxP = Math.ceil(Math.max(...prices) / 100) * 100;
          setMaxPrice(maxP || 2000);
          setPriceLimit(maxP || 2000);
        }
      } catch (err) {
        console.error(err);
        setError("Не вдалося завантажити каталог");
      } finally {
        setLoading(false);
      }
    };
    fetchComponents();
  }, []);

  // --- Скрол-слухач ---
  useEffect(() => {
    const handleScroll = () => setShowScroll(window.scrollY > 400);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  // --- Мемоізована фільтрація ---
  const filteredComponents = useMemo(() => {
    setVisibleCount(ITEMS_PER_PAGE);
    
    return components.filter((comp) => {
      const matchSearch = comp.name.toLowerCase().includes(debouncedSearch.toLowerCase());
      const matchCategory = selectedCategory === "all" || comp.category === selectedCategory;
      const matchPrice = comp.price <= priceLimit;
      return matchSearch && matchCategory && matchPrice;
    });
  }, [components, debouncedSearch, selectedCategory, priceLimit]);

  const categories = useMemo(() => {
    const unique = ["all", ...new Set(components.map((c) => c.category))];
    return unique.sort((a, b) => {
      if (a === "all") return -1;
      if (b === "all") return 1;
      return (CATEGORY_TRANSLATIONS[a] || a).localeCompare(CATEGORY_TRANSLATIONS[b] || b);
    });
  }, [components]);

  // --- Відображуваний список ---
  const displayedComponents = filteredComponents.slice(0, visibleCount);
  const hasMore = visibleCount < filteredComponents.length;

  const bgPattern = {
    backgroundImage: `radial-gradient(circle at 14px 14px, #fef08a 3px, transparent 4px), radial-gradient(circle at 16px 16px, #ca8a04 6px, transparent 7px)`,
    backgroundSize: "32px 32px"
  };

  if (loading) return <Loader />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="min-h-screen bg-[#facc15] font-sans text-slate-900 pb-20 relative overflow-x-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-40" style={bgPattern} />
      
      <div className="relative z-10">
        {/* Header Section */}
        <div className="pt-12 pb-16 px-4 text-center">
          <div className="inline-block bg-white px-8 py-4 rounded-xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] transform -skew-x-3 mb-6">
            <h1 className="text-4xl md:text-6xl font-black italic uppercase text-slate-900 tracking-tighter">
              Каталог <span className="text-red-600 drop-shadow-[2px_2px_0px_#0f172a]">LEGO</span>
            </h1>
          </div>
          <p className="text-slate-900 font-black bg-white/80 backdrop-blur-sm inline-block px-6 py-2 rounded-xl border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] tracking-widest text-sm uppercase">
            Вся база деталей для ваших проєктів в одному місці
          </p>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* STICKY FILTER BAR*/}
          <div className="sticky top-20 z-30 mb-12">
            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="bg-white rounded-2xl shadow-[8px_8px_0px_0px_#0f172a] border-4 border-slate-900 p-4"
            >
              <div className="flex flex-col lg:flex-row items-center gap-4 lg:gap-6">
                
                {/* 1. Пошук */}
                <div className="w-full lg:flex-1 relative group">
                  <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-900 group-focus-within:text-blue-600 transition-colors" />
                  <input
                    type="text"
                    placeholder="Пошук за назвою..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border-2 border-slate-900 rounded-xl focus:outline-none focus:shadow-[4px_4px_0px_0px_#facc15] transition-all text-sm font-bold text-slate-900 placeholder-slate-500 uppercase tracking-wider"
                  />
                </div>

                <div className="hidden lg:block w-1 h-10 bg-slate-900 rounded-full"></div>

                {/* 2. Категорія */}
                <div className="w-full lg:w-64 relative group">
                  <FaFilter className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-900 group-focus-within:text-blue-600 transition-colors" />
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full pl-12 pr-10 py-3 bg-slate-50 border-2 border-slate-900 rounded-xl focus:outline-none focus:shadow-[4px_4px_0px_0px_#facc15] transition-all text-sm font-bold appearance-none cursor-pointer uppercase tracking-wider text-slate-900"
                  >
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {CATEGORY_TRANSLATIONS[cat] || cat}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-900 text-xs">▼</div>
                </div>

                <div className="hidden lg:block w-1 h-10 bg-slate-900 rounded-full"></div>

                {/* 3. Ціна */}
                <div className="w-full lg:w-72 px-2">
                  <div className="flex justify-between text-xs font-black uppercase tracking-widest text-slate-900 mb-2">
                    <span className="flex items-center gap-1.5"><FaTags /> Бюджет до</span>
                    <span className="bg-blue-500 text-white px-2 py-0.5 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">{priceLimit} ₴</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={maxPrice}
                    step={50}
                    value={priceLimit}
                    onChange={(e) => setPriceLimit(Number(e.target.value))}
                    className="w-full h-4 bg-slate-200 border-2 border-slate-900 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>

              </div>
            </motion.div>
          </div>

          {/* Результати */}
          {displayedComponents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32 text-center">
              <div className="w-24 h-24 bg-white border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] rounded-full flex items-center justify-center mb-6">
                <FaBoxOpen className="text-5xl text-slate-400" />
              </div>
              <h3 className="text-2xl font-black uppercase tracking-widest text-slate-900 mb-2 bg-white px-4 py-1 rounded-lg border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] inline-block">Нічого не знайдено</h3>
              <button 
                onClick={() => {setSearchTerm(""); setSelectedCategory("all"); setPriceLimit(maxPrice)}}
                className="mt-6 px-6 py-3 bg-red-500 border-2 border-slate-900 text-white font-black uppercase tracking-widest rounded-xl hover:bg-red-600 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all"
              >
                Скинути всі фільтри
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <AnimatePresence mode="popLayout">
                  {displayedComponents.map((c) => (
                    <motion.div 
                      key={`${c.id}`}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ComponentCard component={c} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Кнопка "Показати ще" */}
              {hasMore && (
                <div className="mt-16 mb-10 text-center">
                  <button 
                    onClick={() => setVisibleCount(prev => prev + ITEMS_PER_PAGE)}
                    className="px-8 py-4 bg-white border-4 border-slate-900 text-slate-900 font-black uppercase tracking-widest text-lg rounded-xl hover:bg-slate-100 shadow-[8px_8px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 hover:shadow-[4px_4px_0px_0px_#0f172a] transition-all active:scale-95"
                  >
                    Показати ще ({filteredComponents.length - visibleCount})
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Кнопка "Вгору" */}
        <AnimatePresence>
          {showScroll && (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              onClick={scrollToTop}
              className="fixed z-50 bottom-8 right-8 p-4 bg-blue-600 text-white rounded-full border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] hover:bg-blue-500 hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all duration-300 active:scale-90"
            >
              <FaArrowUp size={20} />
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// --- Допоміжні компоненти ---

const Loader = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-[#facc15]">
    <div className="relative w-20 h-20 bg-white border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] rounded-2xl flex items-center justify-center animate-bounce">
      <div className="absolute inset-0 border-4 border-blue-600 rounded-xl border-t-transparent animate-spin m-2"></div>
    </div>
    <p className="mt-6 text-slate-900 font-black uppercase tracking-widest bg-white px-4 py-1 border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] rounded-lg">Завантаження...</p>
  </div>
);

const ErrorState = ({ message }: { message: string }) => (
  <div className="min-h-screen flex items-center justify-center bg-[#facc15] p-4">
    <div className="bg-white p-8 rounded-2xl shadow-[8px_8px_0px_0px_#0f172a] border-4 border-slate-900 text-center max-w-md">
      <div className="w-16 h-16 bg-red-500 text-white border-4 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] rounded-full flex items-center justify-center mx-auto mb-6 text-3xl font-black">!</div>
      <h3 className="font-black text-2xl uppercase tracking-widest text-slate-900 mb-2">Помилка</h3>
      <p className="text-slate-600 font-bold mb-6">{message}</p>
      <button onClick={() => window.location.reload()} className="bg-blue-600 text-white px-6 py-3 rounded-xl border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] font-black uppercase tracking-wider hover:bg-blue-500 transition-all hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a]">
        Оновити сторінку
      </button>
    </div>
  </div>
);