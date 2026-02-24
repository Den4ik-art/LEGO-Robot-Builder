
import React from 'react';

interface CyberButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger';
    isLoading?: boolean;
}

export const CyberButton: React.FC<CyberButtonProps> = ({
    children,
    variant = 'primary',
    isLoading,
    className = '',
    ...props
}) => {
    const baseStyles = "relative px-6 py-3 font-display font-bold uppercase tracking-wider transition-all duration-300 transform active:scale-95 clip-corner-br disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
        primary: "bg-neon-yellow text-black hover:bg-yellow-400 hover:shadow-[0_0_15px_rgba(255,255,0,0.6)] border border-transparent",
        secondary: "bg-transparent text-neon-yellow border border-neon-yellow hover:bg-neon-yellow/10 hover:shadow-[0_0_10px_rgba(255,255,0,0.3)]",
        danger: "bg-transparent text-neon-red border border-neon-red hover:bg-neon-red/10 hover:shadow-[0_0_10px_rgba(255,51,51,0.3)]",
    };

    return (
        <button
            className={`${baseStyles} ${variants[variant]} ${className}`}
            disabled={isLoading || props.disabled}
            {...props}
        >
            {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                    PROCESSING...
                </span>
            ) : children}

            {/* Decorative corner element */}
            <div className="absolute bottom-0 right-0 w-2 h-2 bg-current opacity-50" />
        </button>
    );
};
