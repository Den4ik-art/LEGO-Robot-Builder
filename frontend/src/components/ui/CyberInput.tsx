
import React from 'react';

interface CyberInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label: string;
    error?: string;
}

export const CyberInput: React.FC<CyberInputProps> = ({ label, error, className = '', ...props }) => {
    return (
        <div className={`mb-4 group ${className}`}>
            <label className="block text-xs font-display text-neon-yellow mb-1 uppercase tracking-wider opacity-80 group-focus-within:opacity-100 transition-opacity">
                {label}
            </label>
            <div className="relative">
                <input
                    className={`w-full bg-hud-gray/50 border border-gray-700 text-hud-text px-4 py-3 focus:outline-none focus:border-neon-yellow focus:ring-1 focus:ring-neon-yellow/50 transition-all font-mono placeholder-gray-600 ${error ? 'border-neon-red focus:border-neon-red focus:ring-neon-red/50' : ''}`}
                    {...props}
                />
                {/* Animated accent line */}
                <div className="absolute bottom-0 left-0 h-[1px] w-0 bg-neon-yellow group-focus-within:w-full transition-all duration-500 ease-out" />
            </div>
            {error && (
                <div className="mt-1 text-xs text-neon-red flex items-center gap-1 font-mono">
                    <span>⚠</span> {error}
                </div>
            )}
        </div>
    );
};
