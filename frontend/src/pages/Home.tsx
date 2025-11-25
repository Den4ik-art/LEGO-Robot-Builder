import React, { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
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

// --- Анімація ---
const listVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1, 
    transition: { duration: 0.4, ease: "easeOut" } 
  }
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

  if (loading) return <Loader />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800 pb-20">
      
      {/* Header */}
      <div className="relative bg-white pt-8 pb-16 px-4 mb-4 overflow-hidden">
         <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-blue-50/60 rounded-full blur-3xl -z-10 pointer-events-none"></div>
         <div className="max-w-7xl mx-auto text-center z-10 relative">
           <motion.h1 
             initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
             className="text-3xl md:text-5xl font-black text-slate-900 mb-3 tracking-tight"
           >
             Каталог <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">LEGO</span>
           </motion.h1>
           <motion.p 
             initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
             className="text-slate-500 font-medium max-w-lg mx-auto"
           >
             Вся база деталей для ваших проєктів в одному місці.
           </motion.p>
         </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative -mt-12">
        
        {/* STICKY FILTER BAR*/}
        <div className="sticky top-20 z-30 mb-10">
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="bg-white rounded-2xl shadow-xl shadow-slate-200/60 border border-slate-100 p-3"
          >
            <div className="flex flex-col lg:flex-row items-center gap-4 lg:gap-6">
              
              {/* 1. Пошук */}
              <div className="w-full lg:flex-1 relative group">
                <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                <input
                  type="text"
                  placeholder="Пошук за назвою"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 hover:bg-slate-100 focus:bg-white border-0 rounded-xl focus:ring-2 focus:ring-blue-100 transition-all text-sm font-medium text-slate-700 placeholder-slate-400 outline-none"
                />
              </div>

              <div className="hidden lg:block w-px h-10 bg-slate-200"></div>

              {/* 2. Категорія */}
              <div className="w-full lg:w-64 relative group">
                <FaFilter className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full pl-11 pr-10 py-3 bg-slate-50 hover:bg-slate-100 focus:bg-white border-0 rounded-xl focus:ring-2 focus:ring-blue-100 transition-all text-sm font-medium appearance-none cursor-pointer capitalize text-slate-700 outline-none"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {CATEGORY_TRANSLATIONS[cat] || cat}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 text-xs">▼</div>
              </div>

              <div className="hidden lg:block w-px h-10 bg-slate-200"></div>

              {/* 3. Ціна */}
              <div className="w-full lg:w-72 px-2">
                <div className="flex justify-between text-xs font-bold text-slate-500 mb-2">
                  <span className="flex items-center gap-1.5"><FaTags className="text-slate-400"/> Бюджет до</span>
                  <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-md border border-blue-100">{priceLimit} ₴</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={maxPrice}
                  step={50}
                  value={priceLimit}
                  onChange={(e) => setPriceLimit(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-500 transition-all"
                />
              </div>

            </div>
          </motion.div>
        </div>

        {/* Результати */}
        {displayedComponents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-center animate-fadeIn">
            <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mb-6">
              <FaBoxOpen className="text-5xl text-slate-300" />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Нічого не знайдено</h3>
            <p className="text-slate-500 max-w-xs mx-auto">Спробуйте змінити пошуковий запит або категорію.</p>
            <button 
              onClick={() => {setSearchTerm(""); setSelectedCategory("all"); setPriceLimit(maxPrice)}}
              className="mt-6 px-6 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-600 font-bold hover:bg-slate-50 hover:border-slate-400 transition-all shadow-sm"
            >
              Скинути всі фільтри
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              <AnimatePresence mode="popLayout">
                {displayedComponents.map((c, index) => (
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
                  className="px-8 py-3 bg-white border-2 border-blue-100 text-blue-600 font-bold rounded-xl hover:bg-blue-50 hover:border-blue-200 transition-all shadow-sm hover:shadow-md active:scale-95"
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
            className="fixed z-50 bottom-8 right-8 p-4 bg-slate-900 text-white rounded-full shadow-2xl hover:bg-blue-600 hover:-translate-y-1 transition-all duration-300 active:scale-90"
          >
            <FaArrowUp size={20} />
          </motion.button>
        )}
      </AnimatePresence>

    </div>
  );
}

// --- Допоміжні компоненти ---

const Loader = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
    <div className="relative w-16 h-16">
      <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
      <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
    </div>
    <p className="mt-6 text-slate-500 font-medium animate-pulse">Завантаження каталогу...</p>
  </div>
);

const ErrorState = ({ message }: { message: string }) => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
    <div className="bg-white p-8 rounded-2xl shadow-xl border border-red-100 text-center max-w-md">
      <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">!</div>
      <h3 className="font-bold text-xl text-slate-900 mb-2">Виникла помилка</h3>
      <p className="text-slate-500 mb-6">{message}</p>
      <button onClick={() => window.location.reload()} className="bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800 transition">
        Оновити сторінку
      </button>
    </div>
  </div>
);