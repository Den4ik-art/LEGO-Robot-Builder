import React, { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimes } from "react-icons/fa";

type ToastType = "success" | "error" | "info";

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within a ToastProvider");
  return context;
};

// Конфігурація стилів для різних типів
const toastStyles = {
  success: {
    bg: "bg-emerald-50 border-emerald-200",
    icon: <FaCheckCircle className="text-emerald-500 text-xl" />,
    text: "text-emerald-800",
    progress: "bg-emerald-500"
  },
  error: {
    bg: "bg-red-50 border-red-200",
    icon: <FaExclamationCircle className="text-red-500 text-xl" />,
    text: "text-red-800",
    progress: "bg-red-500"
  },
  info: {
    bg: "bg-blue-50 border-blue-200",
    icon: <FaInfoCircle className="text-blue-500 text-xl" />,
    text: "text-blue-800",
    progress: "bg-blue-500"
  }
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toast, setToast] = useState<{ message: string; type: ToastType, id: number } | null>(null);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Date.now();
    setToast({ message, type, id });
    
    // Автоматичне закриття через 3 секунди
    setTimeout(() => {
      setToast((current) => (current?.id === id ? null : current));
    }, 3000);
  }, []);

  const closeToast = () => setToast(null);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      
      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
            className="fixed top-6 right-4 left-4 md:left-auto md:right-6 md:w-auto z-50 flex justify-center pointer-events-none"
          >
            <div 
              className={`
                pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl border backdrop-blur-sm relative overflow-hidden min-w-[300px] max-w-sm
                ${toastStyles[toast.type].bg}
              `}
            >
              {/* Іконка */}
              <div className="mt-0.5 flex-shrink-0">
                {toastStyles[toast.type].icon}
              </div>

              {/* Текст */}
              <div className={`flex-1 text-sm font-medium ${toastStyles[toast.type].text}`}>
                {toast.message}
              </div>

              {/* Кнопка закриття */}
              <button 
                onClick={closeToast}
                className={`ml-2 p-1 rounded-md transition-colors hover:bg-black/5 ${toastStyles[toast.type].text}`}
              >
                <FaTimes />
              </button>

              {/* Прогрес-бар (таймер) */}
              <motion.div 
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 3, ease: "linear" }}
                className={`absolute bottom-0 left-0 h-1 ${toastStyles[toast.type].progress}`}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </ToastContext.Provider>
  );
};