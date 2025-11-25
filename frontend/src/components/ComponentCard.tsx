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
    <div className="relative bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-lg transition-shadow animate-fadeIn overflow-hidden flex flex-col h-full">
      {/* Кількость у верхньому правому куті */}
      {quantity > 1 && (
        <div className="absolute top-2 right-2 px-2.5 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full shadow-md z-10">
          ×{quantity}
        </div>
      )}

      {/* Зображення */}
      <div className="h-48 sm:h-56 bg-gray-50 flex items-center justify-center overflow-hidden relative">
        <img
          src={imageUrl}
          alt={name}
          className="w-full h-full object-contain p-4 transition-transform duration-300 hover:scale-105"
          loading="lazy"
        />
      </div>

      {/* Контент карти */}
      <div className="p-4 flex flex-col gap-2.5 flex-grow">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 line-clamp-2 leading-snug">
          {name}
        </h3>

        <p className="text-xs uppercase tracking-wide text-blue-600 font-semibold">
          {category}
        </p>

        <div className="mt-auto pt-2 border-t border-gray-100">
          <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
            <span className="flex items-center gap-1" title="Вага однієї деталі">
              <b>{weight}</b> г
            </span>
            <span className="font-bold text-blue-700 text-lg">
              {price} ₴
            </span>
          </div>

          {quantity > 1 && (
            <div className="flex justify-between text-xs text-gray-400">
              <span>Разом: {(weight * quantity).toFixed(1)} г</span>
              <span>{(price * quantity).toFixed(0)} ₴</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComponentCard;