/**
 * SIDEBAR — HWELLBEING (PRODUCTION FINAL)
 */

import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Mic,
  Activity,
  Scan,
  X,
} from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const nav = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard, exact: true },
  { name: "Voice", path: "/voice", icon: Mic },
  { name: "Symptom Checker", path: "/triage", icon: Activity },
  { name: "Skin Analysis", path: "/skin", icon: Scan },
];

export default function Sidebar({ open, setOpen }) {
  const navigate = useNavigate();
  const [isDesktop, setIsDesktop] = useState(false);

  // =========================
  // RESPONSIVE
  // =========================
  useEffect(() => {
    const check = () => setIsDesktop(window.innerWidth >= 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  return (
    <>
      {/* OVERLAY (MOBILE) */}
      {!isDesktop && open && (
        <div
          onClick={() => setOpen(false)}
          className="fixed inset-0 bg-black/30 z-40"
        />
      )}

      {/* SIDEBAR */}
      <motion.aside
        initial={false}
        animate={{
          x: isDesktop ? 0 : open ? 0 : -260,
        }}
        transition={{ duration: 0.25 }}
        className="
          fixed md:static z-50
          w-64 h-screen
          overflow-y-auto
          bg-white/80 dark:bg-gray-900/80
          backdrop-blur-xl
          border-r border-gray-200 dark:border-gray-800
          px-6 py-5 flex flex-col
        "
      >
        {/* CLOSE BUTTON (MOBILE) */}
        {!isDesktop && (
          <button
            onClick={() => setOpen(false)}
            className="mb-4 text-gray-500"
          >
            <X />
          </button>
        )}

        {/* LOGO */}
        <h1
          onClick={() => navigate("/")}
          className="text-xl font-bold text-teal-600 mb-8 cursor-pointer tracking-wide"
        >
          HWELBEING AI
        </h1>

        {/* NAVIGATION */}
        <nav className="space-y-2">
          {nav.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.name}
                to={item.path}
                end={item.exact}
              >
                {({ isActive }) => (
                  <div
                    onClick={() => !isDesktop && setOpen(false)}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition ${
                      isActive
                        ? "bg-teal-500 text-white shadow"
                        : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                    }`}
                  >
                    <Icon size={18} />
                    {item.name}
                  </div>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* FOOTER */}
        <div className="mt-auto pt-6 text-xs text-gray-400">
          © HWELBEING
        </div>
      </motion.aside>
    </>
  );
}