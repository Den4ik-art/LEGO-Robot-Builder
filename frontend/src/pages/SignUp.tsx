import React, { useState } from "react";
import { motion, Variants } from "framer-motion";
import { Link } from "react-router-dom";
import { useToast } from "../components/Toast";
import { FaUser, FaEnvelope, FaLock, FaUserPlus, FaArrowRight } from "react-icons/fa";

const containerVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: "easeOut" },
  },
};

export default function SignUp() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    full_name: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Помилка реєстрації");

      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));

      showToast("Реєстрація успішна! Ласкаво просимо", "success");

      setTimeout(() => {
        window.location.href = "/";
      }, 1500);
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-100 flex items-center justify-center p-4 font-sans">
      
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-white/60"
      >
        
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-500 to-teal-600 p-8 text-center text-white">
          <div className="mx-auto w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center mb-4 shadow-inner">
            <FaUserPlus className="text-3xl text-white" />
          </div>
          <h2 className="text-3xl font-extrabold mb-1 tracking-tight">Створити акаунт</h2>
          <p className="text-emerald-50 text-sm font-medium">Приєднуйся до спільноти LEGO-інженерів</p>
        </div>

        {/* Форма */}
        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            
            {/* Логін */}
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-emerald-500 transition-colors">
                <FaUser />
              </div>
              <input
                type="text"
                name="username"
                placeholder="Логін"
                autoComplete="username"
                value={form.username}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Email */}
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-emerald-500 transition-colors">
                <FaEnvelope />
              </div>
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={form.email}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Повне ім'я */}
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-emerald-500 transition-colors">
                <FaUser />
              </div>
              <input
                type="text"
                name="full_name"
                placeholder="Повне ім’я"
                value={form.full_name}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Пароль */}
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-emerald-500 transition-colors">
                <FaLock />
              </div>
              <input
                type="password"
                name="password"
                placeholder="Пароль"
                autoComplete="new-password"
                value={form.password}
                onChange={handleChange}
                className="w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none font-medium text-gray-700 placeholder-gray-400"
                required
              />
            </div>

            {/* Кнопка */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full py-4 mt-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                 <>
                   <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   Реєстрація...
                 </>
              ) : (
                <>
                  Зареєструватися <FaArrowRight className="text-sm" />
                </>
              )}
            </motion.button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center pt-6 border-t border-gray-100">
            <p className="text-gray-500 text-sm">
              Вже маєте акаунт?{" "}
              <Link 
                to="/signin" 
                className="text-emerald-600 font-bold hover:text-emerald-800 transition-colors underline decoration-transparent hover:decoration-emerald-800 underline-offset-2"
              >
                Увійти
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}