import React from "react";
import { motion, Variants } from "framer-motion";
import { Link } from "react-router-dom";
import { 
  FaPuzzlePiece, 
  FaRocket, 
  FaLightbulb, 
  FaUserGraduate, 
  FaTools, 
  FaGamepad,
  FaGithub,
  FaLinkedin,
  FaCar,
  FaPlane,
  FaShip,
  FaRobot,
  FaSearch,
  FaWater
} from "react-icons/fa";

// --- Анімація ---
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" }
  },
};

export default function About() {
  const bgPattern = {
    backgroundImage: `radial-gradient(circle at 14px 14px, #fef08a 3px, transparent 4px), radial-gradient(circle at 16px 16px, #ca8a04 6px, transparent 7px)`,
    backgroundSize: "32px 32px"
  };

  return (
    <div className="min-h-screen bg-[#facc15] py-16 px-4 sm:px-6 lg:px-8 flex flex-col items-center font-sans relative overflow-x-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-40" style={bgPattern} />
      
      <motion.div
        className="max-w-5xl w-full relative z-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        
        {/* ЗАГОЛОВОК */}
        <motion.div variants={itemVariants} className="text-center mb-16">
          <div className="inline-block bg-white px-8 py-4 rounded-xl border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] transform -skew-x-3 mb-6">
            <h1 className="text-4xl md:text-6xl font-black italic uppercase text-slate-900 tracking-tighter">
              Від ідеї до <span className="text-blue-600 drop-shadow-[2px_2px_0px_#0f172a]">реальної моделі</span>
            </h1>
          </div>
          <br/>
          <p className="text-slate-900 font-black bg-white/80 backdrop-blur-sm inline-block px-6 py-2 rounded-xl border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] tracking-widest text-sm uppercase max-w-2xl mx-auto">
            Інтелектуальний помічник, що перетворює ваші вимоги на готову інженерну специфікацію LEGO
          </p>
        </motion.div>

        {/* ОСНОВНА КАРТКА */}
        <motion.div 
          variants={itemVariants}
          className="bg-white rounded-2xl shadow-[8px_8px_0px_0px_#0f172a] overflow-hidden border-4 border-slate-900 mb-12"
        >
          <div className="grid md:grid-cols-2">
            <div className="p-8 md:p-12 bg-blue-600 border-b-4 md:border-b-0 md:border-r-4 border-slate-900 text-white flex flex-col justify-center">
              <h2 className="text-3xl font-black mb-6 flex items-center gap-3 uppercase tracking-tight italic">
                <FaLightbulb className="text-yellow-300 drop-shadow-[2px_2px_0px_#0f172a]" />
                Головна перевага
              </h2>
              <p className="text-white text-lg font-bold leading-relaxed mb-6">
                Ми знімаємо головний біль на етапі планування. Замість годин, витрачених на порівняння характеристик моторів та пошук сумісних деталей, ви отримуєте готове інженерне рішення за секунди.
              </p>
              <div className="bg-white/20 rounded-xl p-4 border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a]">
                <p className="font-black uppercase tracking-wider text-sm">
                  Ви зосереджуєтесь на творчості, збірці та програмуванні. Рутину ми беремо на себе.
                </p>
              </div>
            </div>

            <div className="p-8 md:p-12 text-slate-900 bg-white flex flex-col justify-center">
              <p className="mb-6 text-lg font-bold">
                <strong>LEGO Configurator</strong> — це не просто каталог. Це алгоритмічна система, що використовує <em>жадібний алгоритм</em> та <em>генетичний алгоритм</em> для багато-критеріальної оптимізації.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white font-black flex items-center justify-center mt-1">✓</span>
                  <span className="font-bold">Підбір під конкретні функції (їзда, політ, плавання).</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white font-black flex items-center justify-center mt-1">✓</span>
                  <span className="font-bold">Урахування бюджету та вагових обмежень.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white font-black flex items-center justify-center mt-1">✓</span>
                  <span className="font-bold">Пріоритезація швидкості, потужності або ціни.</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* ЩО МОЖНА ЗІБРАТИ */}
        <motion.div variants={itemVariants} className="mb-16">
          <h3 className="text-3xl font-black uppercase tracking-widest text-slate-900 text-center mb-10 bg-white inline-block px-6 py-2 border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] transform rotate-1 mx-auto block w-max">Основні цільові функції</h3>
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* Картка 1 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:-translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-blue-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaCar size={24} />
              </div>
              <h4 className="text-lg font-black uppercase tracking-tight text-slate-900 mb-2">Їздити</h4>
              <p className="text-slate-600 font-bold text-xs">
                Колісні шасі, гусеничні всюдиходи.
              </p>
            </div>
            {/* Картка 2 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:-translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-sky-400 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaPlane size={24} />
              </div>
              <h4 className="text-lg font-black uppercase tracking-tight text-slate-900 mb-2">Літати</h4>
              <p className="text-slate-600 font-bold text-xs">
                Квадрокоптери, гелікоптери та літаки.
              </p>
            </div>
            {/* Картка 3 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:-translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-teal-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaWater size={24} />
              </div>
              <h4 className="text-lg font-black uppercase tracking-tight text-slate-900 mb-2">Плавати</h4>
              <p className="text-slate-600 font-bold text-xs">
                Гребні гвинти, водомети, плавники.
              </p>
            </div>
            {/* Картка 4 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:-translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-red-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaRobot size={24} />
              </div>
              <h4 className="text-lg font-black uppercase tracking-tight text-slate-900 mb-2">Маніпулювати</h4>
              <p className="text-slate-600 font-bold text-xs">
                Клішні, лінійні актуатори, біонічні руки.
              </p>
            </div>
            {/* Картка 5 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:-translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-purple-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaSearch size={24} />
              </div>
              <h4 className="text-lg font-black uppercase tracking-tight text-slate-900 mb-2">Сканувати</h4>
              <p className="text-slate-600 font-bold text-xs">
                Радари, розвідувальні модулі, аналізатори.
              </p>
            </div>
          </div>
        </motion.div>

        {/* ДЛЯ КОГО ЦЕ */}
        <motion.div variants={itemVariants} className="mb-16">
          <h3 className="text-3xl font-black uppercase tracking-widest text-slate-900 text-center mb-10 bg-white inline-block px-6 py-2 border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] transform -rotate-1 mx-auto block w-max">Для кого цей інструмент?</h3>
          <div className="grid md:grid-cols-3 gap-6">
            {/* Картка 1 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-orange-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaUserGraduate size={24} />
              </div>
              <h4 className="text-xl font-black uppercase tracking-tight text-slate-900 mb-2">Освіта та STEM</h4>
              <p className="text-slate-600 font-bold text-sm">
                Ідеально для студентів, курсових робіт та робототехнічних гуртків. Плануйте проєкти точно та без зайвих витрат.
              </p>
            </div>

            {/* Картка 2 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-purple-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaTools size={24} />
              </div>
              <h4 className="text-xl font-black uppercase tracking-tight text-slate-900 mb-2">Мейкери та AFOLs</h4>
              <p className="text-slate-600 font-bold text-sm">
                Для дорослих фанатів LEGO, які хочуть втілити складну механічну ідею (MOC), не витрачаючи тижні на Excel-таблиці.
              </p>
            </div>

            {/* Картка 3 */}
            <div className="bg-white p-6 rounded-2xl shadow-[6px_6px_0px_0px_#0f172a] border-4 border-slate-900 hover:translate-y-1 hover:translate-x-1 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all">
              <div className="w-12 h-12 bg-pink-500 border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white rounded-xl flex items-center justify-center mb-4">
                <FaGamepad size={24} />
              </div>
              <h4 className="text-xl font-black uppercase tracking-tight text-slate-900 mb-2">Змагання</h4>
              <p className="text-slate-600 font-bold text-sm">
                Швидке прототипування шасі чи маніпуляторів під регламент змагань. Перемагає той, хто краще підготувався.
              </p>
            </div>
          </div>
        </motion.div>

        {/* ПРО АВТОРА */}
        <motion.div variants={itemVariants} className="bg-white rounded-2xl p-8 md:p-12 shadow-[8px_8px_0px_0px_#0f172a] border-4 border-slate-900 relative overflow-hidden">
          
          <div className="flex flex-col md:flex-row items-center gap-10 relative z-10">
            
            {/* Фото (Placeholder) */}
            <motion.div 
              className="relative group"
              whileHover={{ scale: 1.02 }}
            >
              <div className="w-48 h-48 bg-slate-200 border-4 border-slate-900 shadow-[6px_6px_0px_0px_#0f172a] rounded-full overflow-hidden flex items-center justify-center text-slate-400">
                 <FaPuzzlePiece size={64} className="opacity-50" />
              </div>
              <div className="absolute bottom-2 right-2 bg-blue-500 p-2 rounded-full border-2 border-slate-900 shadow-[2px_2px_0px_0px_#0f172a] text-white">
                <FaPuzzlePiece size={20} />
              </div>
            </motion.div>

            {/* Текст */}
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-3xl font-black text-slate-900 mb-2 uppercase tracking-tight">Денис Гаватюк</h2>
              <p className="text-blue-600 font-black uppercase tracking-widest text-sm mb-4 bg-blue-100 inline-block px-3 py-1 rounded border-2 border-slate-900">Full Stack Developer | LEGO Enthusiast</p>
              
              <p className="text-slate-700 font-bold mb-4 leading-relaxed">
                Цей проєкт розроблений як дипломна робота на Кафедрі інтелектуальних технологій <strong>ФІТ КНУ імені Тараса Шевченка</strong>.
              </p>
              <p className="text-slate-700 font-bold mb-6 leading-relaxed">
                Поєднуючи пристрасть до робототехніки та навички у <strong>React</strong>, <strong>Python (FastAPI)</strong> та алгоритмізації, я мав на меті створити інструмент, що долає розрив між сухими академічними алгоритмами та захоплюючим світом інженерії.
              </p>

              {/* Соціальні кнопки */}
              <div className="flex justify-center md:justify-start gap-4">
                <a href="#" className="p-3 bg-white border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] rounded-xl text-slate-900 hover:bg-[#facc15] hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all"><FaGithub size={24}/></a>
                <a href="#" className="p-3 bg-white border-2 border-slate-900 shadow-[4px_4px_0px_0px_#0f172a] rounded-xl text-blue-600 hover:bg-blue-100 hover:translate-y-0.5 hover:translate-x-0.5 hover:shadow-[2px_2px_0px_0px_#0f172a] transition-all"><FaLinkedin size={24}/></a>
              </div>
            </div>
          </div>
        </motion.div>

        {/* КНОПКА ПОВЕРНЕННЯ */}
        <motion.div variants={itemVariants} className="mt-16 text-center pb-10">
          <Link
            to="/configurator"
            className="inline-flex items-center justify-center px-8 py-4 text-lg font-black uppercase tracking-widest text-slate-900 transition-all duration-200 bg-white border-4 border-slate-900 shadow-[8px_8px_0px_0px_#0f172a] rounded-xl hover:bg-slate-100 hover:translate-y-1 hover:translate-x-1 hover:shadow-[4px_4px_0px_0px_#0f172a] transform"
          >
            ← Створити свою конфігурацію
          </Link>
        </motion.div>

      </motion.div>
    </div>
  );
}