// src/App.tsx
import { Routes, Route } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Configurator from "./pages/Configurator";
import About from "./pages/About";
import SignUp from "./pages/SignUp";
import SignIn from "./pages/SignIn";
import History from "./pages/History";
import Home from "./pages/Home";

export default function App() {
  return (
    <Routes>
      {/* Обгортка MainLayout застосовується до внутрішніх сторінок */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/configurator" element={<Configurator />} /> 
        <Route path="/about" element={<About />} />
        <Route path="/history" element={<History />} />
      </Route>

      {/* Сторінки без загального лейауту */}
      <Route path="/signup" element={<SignUp />} />
      <Route path="/signin" element={<SignIn />} />
    </Routes>
  );
}
