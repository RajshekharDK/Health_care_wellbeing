/**
 * HEADER — HWELLBEING (PRODUCTION FINAL UPGRADED)
 */

import { Menu, Moon, LogOut, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import useStore from "../store/useStore";
import { healthAPI } from "../api/api";

export default function Header({ setOpen }) {
  const location = useLocation();
  const navigate = useNavigate();

  const token = useStore((s) => s.token);
  const logout = useStore((s) => s.logout);
  const setError = useStore((s) => s.setError);

  // =========================
  // DARK MODE
  // =========================
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem("theme");
    return stored === "dark";
  });

  useEffect(() => {
    const root = document.documentElement;

    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  // =========================
  // HEALTH STATUS (OPTIMIZED)
  // =========================
  const [health, setHealth] = useState({
    status: "checking",
  });

  useEffect(() => {
    let active = true;

    const fetchHealth = async () => {
      try {
        const res = await healthAPI();
        if (active) setHealth(res);
      } catch {
        if (active) setHealth({ status: "down" });
      }
    };

    fetchHealth();

    const interval = setInterval(fetchHealth, 20000); // slower = better

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // =========================
  // TITLE
  // =========================
  const getTitle = () => {
    const path = location.pathname;

    if (path === "/") return "Dashboard";
    if (path.startsWith("/voice")) return "Voice Consultation";
    if (path.startsWith("/triage")) return "Symptom Checker";
    if (path.startsWith("/skin")) return "Skin Analysis";

    return "HWELLBEING AI";
  };

  const title = getTitle();

  // =========================
  // HEALTH STYLE
  // =========================
  const getHealthStyle = () => {
    if (health.status === "checking")
      return "bg-gray-100 text-gray-500";

    if (!health || health.status === "down")
      return "bg-red-100 text-red-600";

    if (!health.db_connected || !health.models_loaded)
      return "bg-yellow-100 text-yellow-600";

    return "bg-green-100 text-green-600";
  };

  // =========================
  // LOGOUT
  // =========================
  const handleLogout = () => {
    logout();
    setError("Logged out successfully");
    navigate("/login");
  };

  // =========================
  // UI
  // =========================
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="
        flex justify-between items-center px-6 py-4
        bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl
        border-b border-gray-200 dark:border-gray-800
      "
    >
      {/* LEFT */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setOpen(true)}
          className="md:hidden text-teal-600"
        >
          <Menu />
        </button>

        <h1 className="font-semibold text-teal-600 text-lg">
          {title}
        </h1>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">
        {/* HEALTH */}
        <div
          title="System Health"
          className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${getHealthStyle()}`}
        >
          <Activity size={14} />
          {health?.status}
        </div>

        {/* DARK MODE */}
        <button
          onClick={() => setDark((prev) => !prev)}
          className={`transition ${
            dark
              ? "text-yellow-400"
              : "text-gray-500 hover:text-teal-600"
          }`}
        >
          <Moon />
        </button>

        {/* LOGOUT */}
        {token && (
          <button
            onClick={handleLogout}
            className="text-red-500 hover:text-red-600"
            title="Logout"
          >
            <LogOut />
          </button>
        )}

        {/* AVATAR */}
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-teal-400 to-teal-600 shadow-md cursor-pointer" />
      </div>
    </motion.header>
  );
}