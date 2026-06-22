import React from "react";
import type { LegoComponent } from "../types/Component";

const API_URL = "http://127.0.0.1:8000";

type Props = {
  component: LegoComponent;
  quantity?: number;
};

const ComponentCard: React.FC<Props> = ({ component, quantity = 1 }) => {
  const { name, category, price, weight, image } = component;

  const imageUrl = image ? `${API_URL}${image}` : "/placeholder.jpg";

  return (
    <div className="relative bg-white border-4 border-slate-900 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] hover:shadow-[2px_2px_0px_0px_#0f172a] hover:translate-y-1 hover:translate-x-1 transition-all overflow-hidden flex flex-col h-full group">
      {/* Кількость у верхньому правому куті */}
      {quantity > 1 && (
        <div className="absolute top-2 right-2 px-3 py-1 bg-red-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white text-xs font-black uppercase tracking-widest rounded-xl z-10">
          ×{quantity}
        </div>
      )}

      {/* Зображення */}
      <div className="h-48 sm:h-56 bg-slate-50 flex items-center justify-center overflow-hidden relative border-b-4 border-slate-900">
        {/* pattern */}
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: `radial-gradient(circle at 10px 10px, #0f172a 2px, transparent 2px)`, backgroundSize: "20px 20px" }}></div>
        <img
          src={imageUrl}
          alt={name}
          className="w-full h-full object-contain p-6 relative z-10 transition-transform duration-300 group-hover:scale-110 drop-shadow-xl"
          loading="lazy"
        />
      </div>

      {/* Контент карти */}
      <div className="p-4 flex flex-col gap-2 flex-grow bg-white">
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 bg-slate-100 self-start px-2 py-0.5 rounded border-2 border-slate-900">
          {category}
        </p>
        
        <h3 className="text-base sm:text-lg font-black text-slate-900 line-clamp-2 leading-snug uppercase tracking-tight">
          {name}
        </h3>

        <div className="mt-auto pt-3 border-t-2 border-dashed border-slate-300 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Вага</span>
            <span className="font-bold text-slate-700">{weight} г</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Ціна</span>
            <span className="font-black text-blue-600 text-lg bg-blue-100 px-2 py-0.5 rounded border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a]">{price} ₴</span>
          </div>
        </div>

        {quantity > 1 && (
          <div className="flex justify-between text-xs text-slate-500 font-bold uppercase tracking-wider mt-2 bg-slate-50 p-2 rounded-lg border-2 border-slate-900 border-dashed">
            <span>Разом: {(weight * quantity).toFixed(1)} г</span>
            <span className="text-slate-900">{(price * quantity).toFixed(0)} ₴</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComponentCard;