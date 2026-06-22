import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { FaPuzzlePiece, FaSignOutAlt, FaBars, FaTimes } from "react-icons/fa"; 

export default function Header() {
  const location = useLocation();
  const [user, setUser] = useState<{ username: string; full_name: string } | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Помилка парсингу користувача:", e);
        localStorage.removeItem("user");
      }
    }
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    window.location.href = "/signin";
  };

  const linkClasses = (path: string) =>
    `px-4 py-2 rounded-xl transition duration-200 border-2 font-black uppercase tracking-wider text-sm ${
      location.pathname === path
        ? "bg-slate-900 text-[#facc15] border-slate-900 shadow-[2px_2px_0px_0px_#facc15] translate-y-0.5 translate-x-0.5"
        : "bg-white text-slate-900 border-slate-900 hover:bg-slate-100 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a]"
    }`;

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <header className="bg-[#facc15] border-b-4 border-slate-900 sticky top-0 z-50 shadow-[0px_8px_0px_0px_#0f172a]">
      {/* Background Pattern */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `
            radial-gradient(circle at 14px 14px, #ca8a04 3px, transparent 4px),
            radial-gradient(circle at 16px 16px, #a16207 6px, transparent 7px)
          `,
          backgroundSize: "32px 32px"
        }}
      />
      
      <div className="container mx-auto flex justify-between items-center py-3 px-4 lg:px-8 relative z-10">
        
        {/* Логотип */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="p-2 bg-red-600 text-white rounded-lg border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] transform group-hover:rotate-12 transition-transform duration-300">
            <FaPuzzlePiece size={24} /> 
          </div>
          <span className="text-2xl font-black text-slate-900 tracking-tighter uppercase italic">
            LEGO <span className="text-red-600 drop-shadow-[2px_2px_0px_#0f172a]">Configurator</span>
          </span>
        </Link>

        {/* Навігація (центр) */}
        <nav className="hidden lg:flex items-center gap-4">
          <Link to="/" className={linkClasses("/")}>Головна</Link>
          <Link to="/configurator" className={linkClasses("/configurator")}>Конфігуратор</Link>
          <Link to="/history" className={linkClasses("/history")}>Історія</Link>
          <Link to="/analysis" className={linkClasses("/analysis")}>Аналіз</Link>
          <Link to="/about" className={linkClasses("/about")}>Про нас</Link>
        </nav>

        {/* Користувач (праворуч) */}
        <div className="hidden lg:flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end bg-white px-3 py-1 rounded-xl border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]">
                <span className="text-sm font-black text-slate-900 uppercase">
                  {user.full_name || user.username}
                </span>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Користувач</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-xl hover:bg-red-600 transition-colors font-black text-sm uppercase tracking-wider border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a]"
                title="Вийти"
              >
                <FaSignOutAlt />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <Link 
                to="/signin" 
                className="text-slate-900 hover:text-red-600 font-black uppercase tracking-wider transition-colors px-2"
              >
                Увійти
              </Link>
              <Link
                to="/signup"
                className="bg-green-500 text-white px-5 py-2 rounded-xl hover:bg-green-600 transition-all font-black uppercase tracking-wider border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a]"
              >
                Реєстрація
              </Link>
            </div>
          )}
        </div>

        {/* Мобільне меню (гамбургер) */}
        <div className="lg:hidden">
          <button onClick={toggleMobileMenu} className="p-2 bg-white text-slate-900 rounded-lg border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]">
            {mobileMenuOpen ? <FaTimes size={24} /> : <FaBars size={24} />}
          </button>
        </div>
      </div>

      {/* Мобільне випадаюче меню */}
      {mobileMenuOpen && (
        <div className="lg:hidden absolute top-full left-0 w-full bg-white border-b-4 border-slate-900 shadow-[0px_8px_0px_0px_#0f172a] z-40 p-4 flex flex-col gap-4">
          <Link to="/" onClick={toggleMobileMenu} className="font-black uppercase tracking-wider text-slate-900 hover:text-red-600 border-b-2 border-slate-100 pb-2">Головна</Link>
          <Link to="/configurator" onClick={toggleMobileMenu} className="font-black uppercase tracking-wider text-slate-900 hover:text-red-600 border-b-2 border-slate-100 pb-2">Конфігуратор</Link>
          <Link to="/history" onClick={toggleMobileMenu} className="font-black uppercase tracking-wider text-slate-900 hover:text-red-600 border-b-2 border-slate-100 pb-2">Історія</Link>
          <Link to="/analysis" onClick={toggleMobileMenu} className="font-black uppercase tracking-wider text-slate-900 hover:text-red-600 border-b-2 border-slate-100 pb-2">Аналіз</Link>
          <Link to="/about" onClick={toggleMobileMenu} className="font-black uppercase tracking-wider text-slate-900 hover:text-red-600 border-b-2 border-slate-100 pb-2">Про нас</Link>
          
          <div className="pt-2">
            {user ? (
              <div className="flex flex-col gap-3">
                <span className="text-sm font-black text-slate-900 uppercase">
                  Користувач: {user.full_name || user.username}
                </span>
                <button
                  onClick={logout}
                  className="flex items-center justify-center gap-2 bg-red-500 text-white px-4 py-2 rounded-xl font-black text-sm uppercase tracking-wider border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]"
                >
                  <FaSignOutAlt /> Вийти
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <Link 
                  to="/signin" 
                  onClick={toggleMobileMenu}
                  className="text-center bg-white text-slate-900 px-5 py-2 rounded-xl font-black uppercase tracking-wider border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]"
                >
                  Увійти
                </Link>
                <Link
                  to="/signup"
                  onClick={toggleMobileMenu}
                  className="text-center bg-green-500 text-white px-5 py-2 rounded-xl font-black uppercase tracking-wider border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]"
                >
                  Реєстрація
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}