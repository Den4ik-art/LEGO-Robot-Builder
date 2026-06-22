import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useToast } from "../components/Toast";
import { FiUserPlus, FiArrowRight } from "react-icons/fi";

const registerImg = "/images/signup_bg.png";

const LegoBrickIcon = ({ className = "" }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M4 8V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8H4ZM14 18H10V14H14V18ZM8 6V4C8 2.89543 8.89543 2 10 2H14C15.1046 2 16 2.89543 16 4V6H18C19.1046 6 20 6.89543 20 8H4C4 6.89543 4.89543 6 6 6H8Z" />
  </svg>
);

export default function SignUp() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", full_name: "", password: "" });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password || !form.email || !form.full_name) {
      showToast("БУДЬ ЛАСКА, ЗАПОВНІТЬ ВСІ ПОЛЯ", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ПОМИЛКА РЕЄСТРАЦІЇ");
      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));
      showToast("РЕЄСТРАЦІЯ УСПІШНА! ІНІЦІАЛІЗАЦІЯ...", "success");
      setTimeout(() => { window.location.href = "/"; }, 1500);
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#facc15] flex items-center justify-center p-4 md:p-8 relative overflow-hidden font-sans">
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          backgroundImage: `
            radial-gradient(circle at 14px 14px, #fef08a 3px, transparent 4px),
            radial-gradient(circle at 16px 16px, #ca8a04 6px, transparent 7px)
          `,
          backgroundSize: "32px 32px"
        }}
      />
      <div className="w-full max-w-6xl h-auto min-h-[650px] md:min-h-[700px] bg-white rounded-3xl shadow-[16px_16px_0px_0px_#0f172a] relative overflow-hidden flex flex-col md:flex-row border-4 border-slate-900">

        <motion.div initial={{ opacity: 0, x: "-100%" }} animate={{ opacity: 1, x: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="hidden md:block absolute left-0 top-0 bottom-0 w-1/2 overflow-hidden bg-slate-100 border-r-4 border-slate-900">
          <img src={registerImg} alt="Minifigure" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent flex flex-col justify-end p-12">
            <div className="bg-slate-900/80 backdrop-blur-md p-8 rounded-2xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#facc15]">
              <h3 className="text-[#facc15] font-black italic uppercase text-3xl mb-4 tracking-tight drop-shadow-[2px_2px_0px_#0f172a]">Приєднуйтесь до будівництва</h3>
              <p className="text-white font-bold text-sm leading-relaxed uppercase tracking-widest">Почніть свою подорож сьогодні. Розблокуйте передові компоненти та перевірте свої інженерні навички.</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ x: "100%" }} animate={{ x: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="w-full md:w-1/2 h-full p-10 md:px-16 py-16 md:py-24 flex flex-col justify-center bg-white z-10 md:ml-auto"
        >
          <div className="max-w-md w-full mx-auto">
            <motion.div className="flex justify-center mb-6 text-[#facc15]" animate={{ y: [0, -10, 0] }} transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}>
              <LegoBrickIcon className="w-16 h-16 text-blue-600 drop-shadow-[4px_4px_0px_#0f172a]" />
            </motion.div>
            <div className="text-center mb-8 relative">
              <div className="inline-block bg-[#facc15] px-6 py-2 rounded-xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] transform -skew-x-3 mb-4">
                <h2 className="text-3xl font-black italic uppercase text-slate-900 tracking-tighter">НОВА <span className="text-red-600 drop-shadow-[2px_2px_0px_#0f172a]">РЕЄСТРАЦІЯ</span></h2>
              </div>
              <p className="text-slate-900 font-black text-xs tracking-widest uppercase bg-white/80 inline-block px-4 py-1 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">Початок роботи в лабораторії</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-slate-900 font-black uppercase tracking-widest text-xs mb-2">Email</label>
                <input type="email" name="email" value={form.email} onChange={handleChange} className="w-full px-4 py-3 rounded-xl border-4 border-slate-900 bg-white text-slate-900 shadow-[4px_4px_0px_0px_#0f172a] focus:shadow-[8px_8px_0px_0px_#facc15] focus:outline-none transition-all font-bold tracking-wider text-sm" required />
              </div>
              <div>
                <label className="block text-slate-900 font-black uppercase tracking-widest text-xs mb-2">Повне ім'я</label>
                <input type="text" name="full_name" value={form.full_name} onChange={handleChange} className="w-full px-4 py-3 rounded-xl border-4 border-slate-900 bg-white text-slate-900 shadow-[4px_4px_0px_0px_#0f172a] focus:shadow-[8px_8px_0px_0px_#facc15] focus:outline-none transition-all font-bold tracking-wider text-sm" required />
              </div>
              <div>
                <label className="block text-slate-900 font-black uppercase tracking-widest text-xs mb-2">Ім'я користувача</label>
                <input type="text" name="username" value={form.username} onChange={handleChange} className="w-full px-4 py-3 rounded-xl border-4 border-slate-900 bg-white text-slate-900 shadow-[4px_4px_0px_0px_#0f172a] focus:shadow-[8px_8px_0px_0px_#facc15] focus:outline-none transition-all font-bold tracking-wider text-sm" required />
              </div>
              <div>
                <label className="block text-slate-900 font-black uppercase tracking-widest text-xs mb-2">Пароль</label>
                <input type="password" name="password" value={form.password} onChange={handleChange} className="w-full px-4 py-3 rounded-xl border-4 border-slate-900 bg-white text-slate-900 shadow-[4px_4px_0px_0px_#0f172a] focus:shadow-[8px_8px_0px_0px_#facc15] focus:outline-none transition-all font-bold tracking-wider text-sm" required />
              </div>
              <button type="submit" disabled={loading} className="w-full mt-6 bg-blue-600 text-white font-black uppercase tracking-widest text-lg py-4 rounded-xl border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] hover:bg-blue-500 hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all flex items-center justify-center gap-3">
                {loading ? <div className="w-6 h-6 border-4 border-white border-t-transparent rounded-full animate-spin" /> : <><FiUserPlus size={24} />Зареєструвати</>}
              </button>
            </form>
            <div className="mt-8 text-center">
              <button onClick={() => navigate("/signin")} className="text-slate-900 bg-white border-4 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] px-6 py-3 rounded-xl hover:bg-[#facc15] hover:translate-y-1 hover:translate-x-1 hover:shadow-[0px_0px_0px_0px_#0f172a] font-black text-xs tracking-widest uppercase transition-all flex items-center justify-center gap-2 w-full">
                Вже є акаунт? Увійти <FiArrowRight size={16} />
              </button>
            </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
}