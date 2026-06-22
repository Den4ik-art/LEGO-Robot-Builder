import React, { useState } from "react";
import { FaFilePdf, FaSpinner } from "react-icons/fa";
import { useToast } from "./Toast";

interface DownloadPDFButtonProps {
  configId?: number;
  configData?: Record<string, any>;
  className?: string;
  variant?: "small" | "large";
}

/**
 * DownloadPDFButton — завантажує Технічний Паспорт робота (PDF).
 * 
 * Два режими роботи:
 *  1) configId + авторизований — завантажує через /history/{id}/export/pdf
 *  2) configData (будь-який юзер) — генерує PDF напряму через /history/export/pdf/direct
 */
export default function DownloadPDFButton({ configId, configData, className = "", variant = "small" }: DownloadPDFButtonProps) {
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleDownload = async () => {
    setLoading(true);
    try {
      let response: Response;
      const token = localStorage.getItem("token");

      // Стратегія 1: Якщо є configId та авторизація — через БД
      if (configId && configId > 0 && token) {
        response = await fetch(`http://127.0.0.1:8000/history/${configId}/export/pdf`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "token": token,
          },
        });
      }
      // Стратегія 2: Якщо є configData — напряму (без авторизації)
      else if (configData) {
        response = await fetch(`http://127.0.0.1:8000/history/export/pdf/direct`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(configData),
        });
      }
      // Стратегія 3: configId є, але нема токену — спробуємо direct з мінімальними даними
      else {
        showToast("Немає даних для генерації PDF. Спробуйте ще раз.", "error");
        return;
      }

      if (!response.ok) {
        const errText = await response.text();
        let detail = "Не вдалося згенерувати PDF";
        try {
          const errJson = JSON.parse(errText);
          detail = errJson.detail || detail;
        } catch { }
        throw new Error(detail);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `robot_passport_${configId || "config"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      showToast("PDF Технічна Специфікація успішно завантажена!", "success");
    } catch (error: any) {
      console.error("PDF Export Error:", error);
      showToast(error.message || "Помилка при завантаженні PDF", "error");
    } finally {
      setLoading(false);
    }
  };

  if (variant === "large") {
    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          handleDownload();
        }}
        disabled={loading}
        className={`
          flex items-center justify-center gap-3 w-full py-4 px-6
          bg-[#0f172a] text-white border-4 border-slate-900 
          font-black uppercase tracking-widest text-lg rounded-xl
          shadow-[6px_6px_0px_0px_#facc15] hover:bg-slate-800 
          hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#facc15] 
          transition-all disabled:opacity-60 disabled:cursor-not-allowed
          ${className}
        `}
        title="Завантажити Технічну Специфікацію Робота"
      >
        {loading ? (
          <FaSpinner className="animate-spin text-xl" />
        ) : (
          <FaFilePdf className="text-xl text-red-500" />
        )}
        <span>ЗАВАНТАЖИТИ СПЕЦИФІКАЦІЮ (PDF)</span>
      </button>
    );
  }

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        handleDownload();
      }}
      disabled={loading}
      className={`
        flex items-center gap-2 px-4 py-2 
        bg-blue-100 text-blue-900 border-2 border-slate-900 
        font-black uppercase tracking-widest text-xs rounded-xl
        shadow-[3px_3px_0px_0px_#0f172a] hover:bg-blue-200 
        hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[1px_1px_0px_0px_#0f172a] 
        transition-all disabled:opacity-60 disabled:cursor-not-allowed
        ${className}
      `}
      title="Завантажити Технічну Специфікацію (PDF)"
    >
      {loading ? (
        <FaSpinner className="animate-spin text-sm" />
      ) : (
        <FaFilePdf className="text-sm text-red-600" />
      )}
      <span>Завантажити PDF</span>
    </button>
  );
}
