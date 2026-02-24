import React, { useState } from "react";
import { useToast } from "../components/Toast";
import { CyberLayout } from "../components/layout/CyberLayout";
import { CyberCard } from "../components/ui/CyberCard";
import { CyberInput } from "../components/ui/CyberInput";
import { CyberButton } from "../components/ui/CyberButton";
import spacemanImg from "../assets/lego_spaceman_v2.png";
import bgNeon from "../assets/bgSingInUp.jpg";

export default function SignIn() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password) {
      showToast("БУДЬ ЛАСКА, ЗАПОВНІТЬ ВСІ ПОЛЯ", "error");
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

      if (!res.ok) throw new Error(data.detail || "НЕВІРНИЙ ЛОГІН АБО ПАРОЛЬ");

      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));

      showToast("АВТОРИЗАЦІЯ УСПІШНА", "success");

      setTimeout(() => {
        window.location.href = "/";
      }, 1500);
    } catch (err) {
      showToast((err as Error).message, "error");
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

        {/* Absolute Spaceman - Top Right */}
        <div className="hidden lg:block absolute top-[10%] right-[5%] w-[25vw] max-w-[300px] z-20 pointer-events-none">
          <img
            src={spacemanImg}
            alt="Lego Spaceman"
            className="w-full h-auto object-contain drop-shadow-[0_0_20px_rgba(0,191,255,0.6)] animate-pulse-slow"
          />
        </div>

        {/* Content Container */}
        <div className="relative z-10 w-full max-w-md">



          <CyberCard
            title="USER LOGIN"
            variant="yellow"
            className="w-full backdrop-blur-md bg-hud-black/90 shadow-[0_0_50px_rgba(255,255,0,0.15)] border-neon-yellow/30"
          >
            <div className="text-center mb-8">
              <h2 className="text-3xl font-display text-white mb-2 tracking-widest drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
                ВХІД У СИСТЕМУ
              </h2>
              <p className="text-neon-yellow font-mono text-xs tracking-widest uppercase">
                Введіть свої дані для доступу
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6 relative">
              {/* Inner glowing accent */}
              <div className="absolute -inset-4 bg-neon-yellow/5 blurred-3xl rounded-full pointer-events-none" />

              <CyberInput
                label="ІМ'Я КОРИСТУВАЧА"
                name="username"
                value={form.username}
                onChange={handleChange}
                placeholder=""
                disabled={loading}
                className="relative z-10"
              />

              <CyberInput
                label="ПАРОЛЬ"
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder=""
                disabled={loading}
                className="relative z-10"
              />

              <CyberButton
                type="submit"
                variant="primary"
                isLoading={loading}
                className="w-full mt-6 text-lg relative z-10 shadow-[0_0_20px_rgba(255,255,0,0.4)] hover:shadow-[0_0_30px_rgba(255,255,0,0.6)]"
              >
                УВІЙТИ
              </CyberButton>
            </form>

            <div className="mt-8 text-center pt-6 border-t border-gray-800/50">
              <CyberButton
                variant="secondary"
                className="w-full text-xs"
                onClick={() => window.location.href = '/signup'}
              >
                ЩЕ НЕ ЗАРЕЄСТРОВАНІ? РЕЄСТРАЦІЯ
              </CyberButton>
            </div>
          </CyberCard>
        </div>
      </div>
    </CyberLayout>
  );
}