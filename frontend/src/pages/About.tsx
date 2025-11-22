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
  FaLinkedin
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
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-16 px-4 sm:px-6 lg:px-8 flex flex-col items-center font-sans">
      
      <motion.div
        className="max-w-5xl w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        
        {/* === ЗАГОЛОВОК === */}
        <motion.div variants={itemVariants} className="text-center mb-16">
          <div className="inline-flex items-center justify-center p-3 bg-blue-100 text-blue-600 rounded-full mb-4 shadow-sm">
            <FaRocket size={24} />
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold text-slate-800 tracking-tight mb-4">
            Від ідеї до <span className="text-blue-600">реальної моделі</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto">
            Інтелектуальний помічник, що перетворює ваші вимоги на готову інженерну специфікацію LEGO.
          </p>
        </motion.div>

        {/* === ОСНОВНА КАРТКА === */}
        <motion.div 
          variants={itemVariants}
          className="bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-100 mb-12"
        >
          <div className="grid md:grid-cols-2">
            <div className="p-8 md:p-12 bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex flex-col justify-center">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <FaLightbulb className="text-yellow-300" />
                Головна перевага
              </h2>
              <p className="text-blue-100 text-lg leading-relaxed mb-6">
                Ми знімаємо головний біль на етапі планування. Замість годин, витрачених на порівняння характеристик моторів та пошук сумісних деталей, ви отримуєте готове інженерне рішення за секунди.
              </p>
              <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm border border-white/20">
                <p className="font-medium">
                  ✨ Ви зосереджуєтесь на творчості, збірці та програмуванні. Рутину ми беремо на себе.
                </p>
              </div>
            </div>

            <div className="p-8 md:p-12 text-slate-700 flex flex-col justify-center">
              <p className="mb-6 text-lg">
                <strong>LEGO Configurator</strong> — це не просто каталог. Це алгоритмічна система, що використовує <em>жадібний алгоритм</em> та <em>багатокритеріальну оптимізацію</em>.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-1">✓</span>
                  <span>Підбір під конкретні функції (їзда, політ, плавання).</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-1">✓</span>
                  <span>Урахування бюджету та вагових обмежень.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-1">✓</span>
                  <span>Пріоритезація швидкості, потужності або ціни.</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* === ДЛЯ КОГО ЦЕ === */}
        <motion.div variants={itemVariants} className="mb-16">
          <h3 className="text-2xl font-bold text-slate-800 text-center mb-10">Для кого цей інструмент?</h3>
          <div className="grid md:grid-cols-3 gap-6">
            {/* Картка 1 */}
            <div className="bg-white p-6 rounded-2xl shadow-md hover:shadow-lg transition border border-slate-100">
              <div className="w-12 h-12 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center mb-4">
                <FaUserGraduate size={24} />
              </div>
              <h4 className="text-xl font-bold text-slate-800 mb-2">Освіта та STEM</h4>
              <p className="text-slate-600 text-sm">
                Ідеально для студентів, курсових робіт та робототехнічних гуртків. Плануйте проєкти точно та без зайвих витрат.
              </p>
            </div>

            {/* Картка 2 */}
            <div className="bg-white p-6 rounded-2xl shadow-md hover:shadow-lg transition border border-slate-100">
              <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-4">
                <FaTools size={24} />
              </div>
              <h4 className="text-xl font-bold text-slate-800 mb-2">Мейкери та AFOLs</h4>
              <p className="text-slate-600 text-sm">
                Для дорослих фанатів LEGO, які хочуть втілити складну механічну ідею (MOC), не витрачаючи тижні на Excel-таблиці.
              </p>
            </div>

            {/* Картка 3 */}
            <div className="bg-white p-6 rounded-2xl shadow-md hover:shadow-lg transition border border-slate-100">
              <div className="w-12 h-12 bg-pink-100 text-pink-600 rounded-xl flex items-center justify-center mb-4">
                <FaGamepad size={24} />
              </div>
              <h4 className="text-xl font-bold text-slate-800 mb-2">Змагання (FLL/WRO)</h4>
              <p className="text-slate-600 text-sm">
                Швидке прототипування шасі чи маніпуляторів під регламент змагань. Перемагає той, хто краще підготувався.
              </p>
            </div>
          </div>
        </motion.div>

        {/* === ПРО АВТОРА === */}
        <motion.div variants={itemVariants} className="bg-white rounded-3xl p-8 md:p-12 shadow-lg border border-slate-100 relative overflow-hidden">
          {/* Декоративний фон */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full -mr-32 -mt-32 opacity-50 pointer-events-none"></div>
          
          <div className="flex flex-col md:flex-row items-center gap-10 relative z-10">
            
            {/* Фото */}
            <motion.div 
              className="relative group"
              whileHover={{ scale: 1.02 }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              {/* Використовуємо звичайний img для надійності, якщо motion.img дає збої */}
              <img 
                src="/images/avatar.png" 
                alt="Денис Гаватюк"
                className="relative w-48 h-48 object-cover rounded-full border-4 border-white shadow-xl"
              />
              <div className="absolute bottom-2 right-2 bg-white p-2 rounded-full shadow-md text-blue-600">
                <FaPuzzlePiece size={20} />
              </div>
            </motion.div>

            {/* Текст */}
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-3xl font-bold text-slate-800 mb-2">Денис Гаватюк</h2>
              <p className="text-blue-600 font-medium mb-4">Full Stack Developer | LEGO Enthusiast</p>
              
              <p className="text-slate-600 mb-4 leading-relaxed">
                Цей проєкт розроблений як дипломна робота на Кафедрі інтелектуальних технологій <strong>ФІТ КНУ імені Тараса Шевченка</strong>.
              </p>
              <p className="text-slate-600 mb-6 leading-relaxed">
                Поєднуючи пристрасть до робототехніки та навички у <strong>React</strong>, <strong>Python (FastAPI)</strong> та алгоритмізації, я мав на меті створити інструмент, що долає розрив між сухими академічними алгоритмами та захоплюючим світом інженерії.
              </p>

              {/* Соціальні кнопки */}
              <div className="flex justify-center md:justify-start gap-4">
                <a href="#" className="p-2 text-slate-400 hover:text-slate-800 transition"><FaGithub size={24}/></a>
                <a href="#" className="p-2 text-slate-400 hover:text-blue-700 transition"><FaLinkedin size={24}/></a>
              </div>
            </div>
          </div>
        </motion.div>

        {/* === КНОПКА ПОВЕРНЕННЯ === */}
        <motion.div variants={itemVariants} className="mt-16 text-center pb-10">
          <Link
            to="/"
            className="inline-flex items-center justify-center px-8 py-4 text-lg font-bold text-white transition-all duration-200 bg-blue-600 rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 shadow-lg hover:shadow-blue-500/30 transform hover:-translate-y-1"
          >
            ← Створити свою конфігурацію
          </Link>
        </motion.div>

      </motion.div>
    </div>
  );
}