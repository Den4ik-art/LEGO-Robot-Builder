
import React from 'react';

interface CyberCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    variant?: 'yellow' | 'red';
}

export const CyberCard: React.FC<CyberCardProps> = ({
    children,
    className = '',
    title,
    variant = 'yellow'
}) => {
    const borderColor = variant === 'yellow' ? 'border-neon-yellow' : 'border-neon-red';
    const glowColor = variant === 'yellow' ? 'shadow-[0_0_10px_rgba(255,255,0,0.2)]' : 'shadow-[0_0_10px_rgba(255,51,51,0.2)]';
    const textColor = variant === 'yellow' ? 'text-neon-yellow' : 'text-neon-red';
    const bgOpacity = 'bg-hud-black/80';

    return (
        <div className={`relative ${className}`}>
            {/* Background with Clip Path */}
            <div className={`absolute inset-0 ${bgOpacity} backdrop-blur-sm border ${borderColor} ${glowColor} clip-corner-both`}>
                {/* Decorative Corner Lines inside the clipped area */}
                <div className={`absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 ${borderColor} opacity-50`} />
                <div className={`absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 ${borderColor} opacity-50`} />
                <div className={`absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 ${borderColor} opacity-50`} />
                <div className={`absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 ${borderColor} opacity-50`} />
            </div>

            {/* Title (Outside clipped area) */}
            {title && (
                <div className={`absolute -top-3 left-1/2 transform -translate-x-1/2 bg-hud-black px-4 py-0.5 border ${borderColor} rounded-sm z-20`}>
                    <h3 className={`font-display font-bold tracking-widest text-sm ${textColor} uppercase whitespace-nowrap`}>
                        {title}
                    </h3>
                </div>
            )}

            {/* Content */}
            <div className="relative z-10 p-6">
                {children}
            </div>
        </div>
    );
};
