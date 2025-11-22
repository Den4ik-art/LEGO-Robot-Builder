import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { FaPuzzlePiece, FaSignOutAlt } from "react-icons/fa"; // 👈 ВИПРАВЛЕНО: FaLegoBrick -> FaPuzzlePiece

export default function Header() {
  const location = useLocation();
  const [user, setUser] = useState<{ username: string; full_name: string } | null>(null);

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
    `px-4 py-2 rounded-lg transition duration-200 ${
      location.pathname === path
        ? "bg-blue-100 text-blue-700 font-semibold"
        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
    }`;

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50 border-b border-gray-100">
      <div className="container mx-auto flex justify-between items-center py-3 px-4 lg:px-8">
        
        {/* Логотип */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="p-2 bg-blue-600 text-white rounded-lg transform group-hover:rotate-12 transition-transform duration-300">
            <FaPuzzlePiece size={24} /> {/* 👈 Використовуємо коректну іконку */}
          </div>
          <span className="text-xl font-extrabold text-gray-800 tracking-tight group-hover:text-blue-600 transition-colors">
            LEGO <span className="text-blue-600">Configurator</span>
          </span>
        </Link>

        {/* Навігація (центр) */}
        <nav className="hidden md:flex items-center gap-2">
          <Link to="/" className={linkClasses("/")}>
            Головна
          </Link>
          <Link to="/configurator" className={linkClasses("/configurator")}>
            Конфігуратор
          </Link>
          <Link to="/history" className={linkClasses("/history")}>
            Історія
          </Link>
          <Link to="/about" className={linkClasses("/about")}>
            Про нас
          </Link>
        </nav>

        {/* Користувач (праворуч) */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex flex-col items-end">
                <span className="text-sm font-bold text-gray-700 leading-tight">
                  {user.full_name || user.username}
                </span>
                <span className="text-xs text-gray-500">Користувач</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-lg hover:bg-red-100 transition-colors font-medium text-sm"
                title="Вийти"
              >
                <FaSignOutAlt />
                <span className="hidden sm:inline">Вийти</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link 
                to="/signin" 
                className="text-gray-600 hover:text-blue-600 font-medium transition-colors px-2"
              >
                Увійти
              </Link>
              <Link
                to="/signup"
                className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md hover:shadow-lg transform hover:-translate-y-0.5 duration-200"
              >
                Реєстрація
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}