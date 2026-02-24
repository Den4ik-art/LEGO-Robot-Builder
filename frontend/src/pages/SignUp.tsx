import React, { useState } from "react";
import { useToast } from "../components/Toast";
import { CyberLayout } from "../components/layout/CyberLayout";
import { CyberCard } from "../components/ui/CyberCard";
import { CyberInput } from "../components/ui/CyberInput";
import { CyberButton } from "../components/ui/CyberButton";
import spacemanImg from "../assets/lego_spaceman_v2.png";
import bgNeon from "../assets/bgSingInUp.jpg";

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

      if (!res.ok) throw new Error(data.detail || "ПОМИЛКА РЕЄСТРАЦІЇ");

      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));

      showToast("РЕЄСТРАЦІЯ УСПІШНА! ІНІЦІАЛІЗАЦІЯ...", "success");

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
    <CyberLayout>
      <div className="relative w-full h-[80vh] flex items-center justify-center p-4">

        {/* LEGO Background Frame */}
        <div className="fixed inset-0 z-0 flex items-center justify-center pointer-events-none">
          <img
            src={bgNeon}
            alt="Neon Background"
            className="w-full h-full object-cover"
          />
        </div>

        {/* Content Container */}
        <div className="relative z-10 w-full max-w-md">



          <CyberCard
            title="NEW USER REGISTRATION"
            variant="yellow"
            className="w-full backdrop-blur-md bg-hud-black/90 shadow-[0_0_50px_rgba(255,255,0,0.15)] border-neon-yellow/30"
          >
            <div className="text-center mb-6">
              <h2 className="text-2xl font-display text-white mb-2 tracking-wide drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
                РЕЄСТРАЦІЯ
              </h2>
              <p className="text-neon-yellow font-mono text-xs tracking-widest uppercase">
                СТВОРИТИ НОВИЙ АКАУНТ
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 relative">
              <div className="absolute -inset-4 bg-neon-yellow/5 blurred-3xl rounded-full pointer-events-none" />

              <CyberInput
                label="ЛОГІН"
                name="username"
                value={form.username}
                onChange={handleChange}
                placeholder=""
                required
                className="relative z-10"
              />

              <CyberInput
                label="EMAIL"
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder=""
                required
                className="relative z-10"
              />

              <CyberInput
                label="ПОВНЕ ІМ'Я"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                placeholder=""
                required
                className="relative z-10"
              />

              <CyberInput
                label="ПАРОЛЬ"
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder=""
                required
                className="relative z-10"
              />

              <CyberButton
                type="submit"
                variant="primary"
                isLoading={loading}
                className="w-full mt-4 relative z-10 shadow-[0_0_20px_rgba(255,255,0,0.4)] hover:shadow-[0_0_30px_rgba(255,255,0,0.6)]"
              >
                ІНІЦІАЛІЗУВАТИ
              </CyberButton>
            </form>

            <div className="mt-6 text-center pt-4 border-t border-gray-800/50">
              <CyberButton
                variant="danger"
                className="w-full text-xs"
                onClick={() => window.location.href = '/signin'}
              >
                ВЖЕ Є АКАУНТ? УВІЙТИ
              </CyberButton>
            </div>
          </CyberCard>
        </div>
      </div>
    </CyberLayout>
  );
}