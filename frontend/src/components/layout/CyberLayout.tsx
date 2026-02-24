
import React from 'react';

interface CyberLayoutProps {
    children: React.ReactNode;
}

export const CyberLayout: React.FC<CyberLayoutProps> = ({ children }) => {
    return (
        <div className="min-h-screen w-full bg-hud-black bg-circuit-pattern bg-fixed flex flex-col items-center justify-center p-4 relative overflow-hidden">
            {/* Ambient Glow Effects */}
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-neon-yellow/5 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-neon-red/5 rounded-full blur-[100px] pointer-events-none" />

            {/* Scanline Effect */}
            <div className="fixed inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] bg-repeat z-50 opacity-20" />

            {/* Main Content */}
            <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col items-center">
                {children}
            </div>

            {/* Header / Top Left Info */}
            <div className="absolute top-6 left-8 z-50 flex items-center gap-4">
                <img src="/LEGO_logo.svg.png" alt="LEGO" className="h-12 w-auto drop-shadow-[0_0_10px_rgba(255,0,0,0.5)]" />
                <div className="flex flex-col">
                    <h1 className="text-white font-display text-lg tracking-widest leading-none">LEGO CONFIGURATOR</h1>
                    <span className="text-neon-yellow font-mono text-xs tracking-[0.2em] opacity-80">ACCESS TERMINAL</span>
                </div>
            </div>

            {/* Footer / Status Bar - optional decorative element */}
            <div className="fixed bottom-0 w-full bg-hud-black/90 border-t border-gray-800 p-2 flex justify-between text-[10px] text-gray-500 font-mono z-40 px-6">
                <span>SYS.STATUS: ONLINE</span>
                <span>SECURE CONNECTION ESTABLISHED</span>
                <span>© 2026 LEGO CYBERNETICS DIVISION</span>
            </div>
        </div>
    );
};
