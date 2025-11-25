import React, { useState } from "react";
import { motion, Variants } from "framer-motion";
import { Link } from "react-router-dom";
import { useToast } from "../components/Toast";
import { FaUser, FaLock, FaArrowRight, FaSignInAlt } from "react-icons/fa";

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" },
  },
};

export default function SignIn() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password) {
      showToast("Будь ласка, заповніть всі поля", "error");
      return;
    }
    
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Невірний логін або пароль");

      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));

      showToast("Раді вас бачити знову!", "success");

      setTimeout(() => {
        window.location.href = "/";
      }, 1500);
    } catch (err) {
      showToast((err as Error).message, "error");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 font-sans">
      
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden"
      >
        
        {/* (Header) */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-center text-white">
          <div className="mx-auto w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center mb-4 shadow-inner">
            <FaSignInAlt className="text-3xl text-white" />
          </div>
          <h2 className="text-3xl font-bold mb-2">Вхід в акаунт</h2>
          <p className="text-blue-100 text-sm">Продовжуйте створення свого ідеального робота</p>
        </div>

        {/* Форма */}
        <div className="p-8 pt-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Поле Логін */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                <FaUser />
              </div>
              <input
                type="text"
                name="username"
                placeholder="Ваш логін"
                autoComplete="username"
                value={form.username}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-4 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Поле Пароль */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                <FaLock />
              </div>
              <input
                type="password"
                name="password"
                placeholder="Ваш пароль"
                autoComplete="current-password"
                value={form.password}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-4 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Кнопка входу */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Перевірка...
                </span>
              ) : (
                <>
                  Увійти <FaArrowRight className="text-sm" />
                </>
              )}
            </motion.button>
          </form>

          {/* Підвал форми */}
          <div className="mt-8 text-center">
            <p className="text-gray-500 text-sm">
              Немає акаунту?{" "}
              <Link 
                to="/signup" 
                className="text-blue-600 font-bold hover:text-blue-800 transition-colors underline decoration-transparent hover:decoration-blue-800 underline-offset-2"
              >
                Зареєструватися
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
      
    </div>
  );
}