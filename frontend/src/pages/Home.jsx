/**
 * HOME PAGE — HWELLBEING (PREMIUM PRODUCTION UI)
 */

import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-[#ecfeff] via-white to-[#f0fdfa] text-gray-800">

      {/* GOOGLE ICONS */}
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
        rel="stylesheet"
      />

      {/* =========================
          BACKGROUND GLOW
      ========================= */}
      <div className="absolute top-[-100px] left-[-100px] w-[400px] h-[400px] bg-teal-300 opacity-20 blur-[120px] rounded-full"></div>
      <div className="absolute bottom-[-120px] right-[-120px] w-[400px] h-[400px] bg-cyan-400 opacity-20 blur-[120px] rounded-full"></div>

      {/* =========================
          HERO
      ========================= */}
      <section className="px-6 md:px-20 py-16 relative z-10">
        <div className="backdrop-blur-2xl bg-white/50 border border-white/40 shadow-2xl rounded-3xl p-10 flex flex-col md:flex-row items-center justify-between">

          <div className="max-w-xl">
            <h1 className="text-5xl font-bold leading-tight mb-5">
              Intelligent Healthcare
              <span className="text-teal-600"> Powered by AI</span>
            </h1>

            <p className="text-gray-600 text-lg mb-6">
              Diagnose faster, interact smarter, and access care instantly — with a unified AI-powered health platform.
            </p>

            <div className="flex gap-4">
              <button
                onClick={() => navigate("/login")}
                className="bg-teal-600 hover:bg-teal-700 transition text-white px-7 py-3 rounded-full shadow-lg"
              >
                Login
              </button>

              <button
                onClick={() => navigate("/register")}
                className="border border-gray-300 hover:border-teal-500 px-7 py-3 rounded-full transition"
              >
                Register
              </button>
            </div>

            {/* TRUST STATS */}
            <div className="flex gap-8 mt-8 text-sm text-gray-500">
              <div>
                <p className="font-bold text-gray-800">99%</p>
                Accuracy
              </div>
              <div>
                <p className="font-bold text-gray-800">Realtime</p>
                AI Engine
              </div>
              <div>
                <p className="font-bold text-gray-800">Secure</p>
                JWT System
              </div>
            </div>
          </div>

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-8xl text-teal-500 mt-10 md:mt-0 drop-shadow-xl"
          >
            <span className="material-symbols-outlined text-[90px]">
              monitor_heart
            </span>
          </motion.div>
        </div>
      </section>

      {/* =========================
          FEATURES
      ========================= */}
      <section className="px-6 md:px-20 py-12 grid md:grid-cols-4 gap-6">

        {[
          { title: "Triage AI", icon: "psychology", desc: "ML-based disease prediction" },
          { title: "Voice AI", icon: "mic", desc: "Conversational health assistant" },
          { title: "Skin AI", icon: "dermatology", desc: "CNN-powered detection" },
          { title: "Doctor Finder", icon: "local_hospital", desc: "Location-based discovery" },
        ].map((item, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.06 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="group backdrop-blur-xl bg-white/60 border border-white/30 rounded-2xl p-6 shadow-md hover:shadow-xl transition"
          >
            <span className="material-symbols-outlined text-4xl text-teal-600 group-hover:scale-110 transition">
              {item.icon}
            </span>

            <h3 className="font-semibold mt-4 text-lg">{item.title}</h3>
            <p className="text-sm text-gray-500 mt-2">{item.desc}</p>
          </motion.div>
        ))}
      </section>

      {/* =========================
          SYSTEM INFO
      ========================= */}
      <section className="px-6 md:px-20 py-12">
        <div className="backdrop-blur-xl bg-white/60 border border-white/30 rounded-3xl p-10 shadow-lg">

          <h2 className="text-2xl font-semibold mb-6">
            Platform Capabilities
          </h2>

          <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">

            {[
              "AI triage using machine learning",
              "Real-time voice conversation (WebSocket)",
              "Skin disease detection (CNN)",
              "Nearby doctor discovery (OSM)",
              "JWT-secured authentication",
              "Async FastAPI backend",
              "Multi-language support",
              "Optimized caching architecture"
            ].map((text, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="material-symbols-outlined text-teal-500">
                  verified
                </span>
                {text}
              </div>
            ))}

          </div>
        </div>
      </section>

      {/* =========================
          CTA
      ========================= */}
      <section className="px-6 md:px-20 py-14 text-center">

        <div className="backdrop-blur-2xl bg-gradient-to-r from-teal-600/90 to-cyan-500/90 text-white rounded-3xl p-10 shadow-2xl">

          <h2 className="text-3xl font-semibold mb-4">
            Experience Smarter Healthcare
          </h2>

          <p className="mb-6 opacity-90">
            Join thousands using AI to make better health decisions instantly.
          </p>

          <button
            onClick={() => navigate("/register")}
            className="bg-white text-teal-700 px-8 py-3 rounded-full shadow-lg hover:scale-105 transition"
          >
            Get Started
          </button>
        </div>
      </section>

      {/* =========================
          FOOTER
      ========================= */}
      <footer className="text-center text-xs text-gray-400 pb-8">
        © 2026 HWellbeing • AI Healthcare Platform
      </footer>

    </div>
  );
}