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

// Анімація появи для колонок
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
    <footer className="bg-slate-900 text-slate-300 mt-auto border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-6 py-12 lg:py-16">
        
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          
          {/* === 1. БРЕНД === */}
          <motion.div variants={itemVariants} className="space-y-4">
            <Link to="/" className="flex items-center gap-2 text-white hover:text-blue-400 transition-colors group">
              <FaPuzzlePiece className="text-2xl text-blue-500 group-hover:rotate-12 transition-transform duration-300" />
              <span className="text-xl font-bold tracking-tight">LEGO Configurator</span>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed max-w-xs">
              Інтелектуальний інструмент для інженерів та ентузіастів. 
              Автоматизуйте підбір деталей та створюйте ідеальні моделі без зайвих зусиль.
            </p>
            <div className="flex gap-4 pt-2">
              <SocialLink href="https://github.com/" icon={<FaGithub />} label="GitHub" />
              <SocialLink href="https://linkedin.com/" icon={<FaLinkedin />} label="LinkedIn" />
            </div>
          </motion.div>

          {/* === 2. НАВІГАЦІЯ === */}
          <motion.div variants={itemVariants}>
            <h3 className="text-white font-semibold mb-4">Навігація</h3>
            <ul className="space-y-3 text-sm">
              <FooterLink to="/" label="🚀 Конфігуратор" />
              <FooterLink to="/history" label="📜 Історія запитів" />
              <FooterLink to="/about" label="ℹ️ Про проєкт" />
            </ul>
          </motion.div>

          {/* === 3. АКАУНТ === */}
          <motion.div variants={itemVariants}>
            <h3 className="text-white font-semibold mb-4">Акаунт</h3>
            <ul className="space-y-3 text-sm">
              <FooterLink to="/signin" label="🔑 Вхід" />
              <FooterLink to="/signup" label="📝 Реєстрація" />
              <li className="text-slate-500 text-xs pt-2">
                * Доступ до історії доступний лише авторизованим користувачам.
              </li>
            </ul>
          </motion.div>

          {/* === 4. ТЕХНОЛОГІЇ (STACK) === */}
          <motion.div variants={itemVariants}>
            <h3 className="text-white font-semibold mb-4">Tech Stack</h3>
            <p className="text-xs text-slate-500 mb-4">Побудовано на сучасних технологіях:</p>
            <div className="flex flex-wrap gap-3">
              <TechBadge icon={<SiReact />} label="React" color="text-cyan-400" />
              <TechBadge icon={<SiTypescript />} label="TS" color="text-blue-500" />
              <TechBadge icon={<SiFastapi />} label="FastAPI" color="text-teal-400" />
              <TechBadge icon={<SiTailwindcss />} label="Tailwind" color="text-sky-400" />
              <TechBadge icon={<SiVite />} label="Vite" color="text-purple-400" />
            </div>
          </motion.div>

        </motion.div>

        {/* === НИЖНІЙ БАР === */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-500"
        >
          <p>&copy; {currentYear} LEGO Configurator. Всі права захищені.</p>
          <p className="flex items-center gap-1">
            Розроблено з <FaHeart className="text-red-500 animate-pulse" /> студентом Денисом Гаватюком
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
        className="hover:text-blue-400 hover:pl-1 transition-all duration-200 flex items-center gap-2"
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
      className="bg-slate-800 p-2 rounded-full text-slate-400 hover:text-white hover:bg-blue-600 transition-all duration-300"
      aria-label={label}
    >
      {icon}
    </a>
  );
}

function TechBadge({ icon, label, color }: { icon: React.ReactNode; label: string; color: string }) {
  return (
    <div className={`flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-md border border-slate-700 text-xs font-medium ${color}`}>
      {icon}
      <span className="text-slate-300">{label}</span>
    </div>
  );
}