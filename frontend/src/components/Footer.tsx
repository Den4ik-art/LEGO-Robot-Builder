import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  SiReact, 
  SiFastapi, 
  SiTypescript, 
  SiTailwindcss, 
  SiVite 
} from "react-icons/si";
import { FaGithub, FaLinkedin, FaHeart, FaPuzzlePiece } from "react-icons/fa";

// Анімація
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 text-slate-300 mt-auto border-t-8 border-[#facc15] relative overflow-hidden z-20">
      <div
        className="absolute inset-0 pointer-events-none opacity-5"
        style={{
          backgroundImage: `
            radial-gradient(circle at 14px 14px, #ffffff 3px, transparent 4px),
            radial-gradient(circle at 16px 16px, #ffffff 6px, transparent 7px)
          `,
          backgroundSize: "32px 32px"
        }}
      />
      <div className="max-w-7xl mx-auto px-6 py-12 lg:py-16 relative z-10">
        
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          
          {/* БРЕНД */}
          <motion.div variants={itemVariants} className="space-y-4">
            <Link to="/" className="flex items-center gap-3 text-white group">
              <div className="p-2 bg-red-600 rounded-lg border-2 border-slate-900 shadow-[4px_4px_0px_0px_#facc15] group-hover:rotate-12 transition-transform duration-300">
                <FaPuzzlePiece className="text-xl text-white" />
              </div>
              <span className="text-2xl font-black tracking-tighter uppercase italic text-white group-hover:text-[#facc15] transition-colors">
                LEGO <span className="text-red-500">Config</span>
              </span>
            </Link>
            <p className="text-sm font-bold text-slate-400 leading-relaxed max-w-xs uppercase tracking-wider">
              Інтелектуальний інструмент для інженерів та ентузіастів. Автоматизуйте підбір деталей!
            </p>
            <div className="flex gap-4 pt-2">
              <SocialLink href="https://github.com/" icon={<FaGithub />} label="GitHub" />
              <SocialLink href="https://linkedin.com/" icon={<FaLinkedin />} label="LinkedIn" />
            </div>
          </motion.div>

          {/* НАВІГАЦІЯ */}
          <motion.div variants={itemVariants}>
            <h3 className="text-[#facc15] font-black uppercase tracking-widest mb-4">Навігація</h3>
            <ul className="space-y-3 font-bold text-sm uppercase tracking-wider">
              <FooterLink to="/" label="Конфігуратор" />
              <FooterLink to="/history" label="Історія запитів" />
              <FooterLink to="/about" label="Про проєкт" />
              <FooterLink to="/analysis" label="Аналіз" />
            </ul>
          </motion.div>

          {/* АКАУНТ */}
          <motion.div variants={itemVariants}>
            <h3 className="text-[#facc15] font-black uppercase tracking-widest mb-4">Акаунт</h3>
            <ul className="space-y-3 font-bold text-sm uppercase tracking-wider">
              <FooterLink to="/signin" label="Вхід" />
              <FooterLink to="/signup" label="Реєстрація" />
              <li className="text-slate-500 text-xs pt-2 normal-case tracking-normal">
                * Доступ до історії доступний лише авторизованим користувачам.
              </li>
            </ul>
          </motion.div>

          {/* ТЕХНОЛОГІЇ (STACK) */}
          <motion.div variants={itemVariants}>
            <h3 className="text-[#facc15] font-black uppercase tracking-widest mb-4">Tech Stack</h3>
            <div className="flex flex-wrap gap-3">
              <TechBadge icon={<SiReact />} label="React" color="bg-cyan-500" />
              <TechBadge icon={<SiTypescript />} label="TS" color="bg-blue-600" />
              <TechBadge icon={<SiFastapi />} label="FastAPI" color="bg-teal-600" />
              <TechBadge icon={<SiTailwindcss />} label="Tailwind" color="bg-sky-500" />
              <TechBadge icon={<SiVite />} label="Vite" color="bg-purple-600" />
            </div>
          </motion.div>

        </motion.div>

        {/* НИЖНІЙ БАР */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="pt-8 border-t-2 border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-bold uppercase tracking-widest text-slate-500"
        >
          <p>&copy; {currentYear} LEGO Configurator. Всі права захищені.</p>
          <p className="flex items-center gap-2">
            Розроблено з <FaHeart className="text-red-500 animate-bounce" /> студентом
          </p>
        </motion.div>
      </div>
    </footer>
  );
}

// --- Допоміжні компоненти для чистоти коду ---

function FooterLink({ to, label }: { to: string; label: string }) {
  return (
    <li>
      <Link 
        to={to} 
        className="text-slate-300 hover:text-white hover:bg-slate-800 px-2 py-1 rounded-md transition-all duration-200 flex items-center gap-2 border-2 border-transparent hover:border-slate-700"
      >
        {label}
      </Link>
    </li>
  );
}

function SocialLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer"
      className="bg-white p-2 rounded-xl text-slate-900 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#facc15] hover:bg-[#facc15] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[0px_0px_0px_0px_#facc15] transition-all duration-200"
      aria-label={label}
    >
      {icon}
    </a>
  );
}

function TechBadge({ icon, label, color }: { icon: React.ReactNode; label: string; color: string }) {
  return (
    <div className={`flex items-center gap-1.5 ${color} text-white px-3 py-1.5 rounded-lg border-2 border-slate-900 shadow-[2px_2px_0px_0px_#000] text-xs font-black uppercase tracking-wider`}>
      {icon}
      <span>{label}</span>
    </div>
  );
}