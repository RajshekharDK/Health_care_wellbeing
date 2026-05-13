/**
 * REGISTER PAGE — HWELLBEING (PREMIUM GLASS UI + FIXED + UX UPGRADE)
 */

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";

import { registerAPI } from "../api/api";
import useStore from "../store/useStore";

export default function Register() {
  const navigate = useNavigate();
  const setError = useStore((s) => s.setError);

  const [form, setForm] = useState({
    username: "",
    password: "",
    confirm: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleRegister = async () => {
    const username = form.username.trim();
    const password = form.password.trim();
    const confirm = form.confirm.trim();

    if (!username || !password || !confirm) {
      setError("All fields are required");
      return;
    }

    if (password.length < 4) {
      setError("Password must be at least 4 characters");
      return;
    }

    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await registerAPI(username, password);
      navigate("/login");
    } catch (err) {
      setError(typeof err === "string" ? err : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleRegister();
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-[#ecfeff] via-white to-[#f0fdfa]">

      {/* GOOGLE ICONS */}
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
        rel="stylesheet"
      />

      {/* 🔥 BACK BUTTON (FIXED) */}
      <button
        onClick={() => navigate("/")}
        className="absolute top-6 left-6 z-20 flex items-center gap-2 px-3 py-1.5 rounded-lg 
                   text-sm text-gray-600 hover:text-teal-600 hover:bg-white/50 
                   backdrop-blur-md transition-all duration-200 hover:scale-105 active:scale-95"
      >
        <span className="material-symbols-outlined text-[18px]">
          arrow_back
        </span>
        Home
      </button>

      {/* 🔥 BACKGROUND GLOW (FIXED) */}
      <div className="absolute top-[-120px] left-[-120px] w-[350px] h-[350px] bg-teal-300 opacity-20 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-120px] right-[-120px] w-[350px] h-[350px] bg-cyan-400 opacity-20 blur-[120px] rounded-full pointer-events-none"></div>

      {/* CARD */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 backdrop-blur-2xl bg-white/60 border border-white/40 shadow-2xl rounded-3xl p-10 w-full max-w-md"
      >
        <h2 className="text-3xl font-bold text-center mb-2">
          Create Account
        </h2>

        <p className="text-center text-gray-500 mb-8 text-sm">
          Join the AI-powered healthcare platform
        </p>

        {/* USERNAME */}
        <div className="relative mb-4">
          <span className="material-symbols-outlined absolute left-3 top-3 text-gray-400">
            person
          </span>
          <input
            name="username"
            placeholder="Username"
            className="w-full pl-10 pr-3 py-3 rounded-xl bg-white/70 border border-gray-200 
                       focus:outline-none focus:ring-2 focus:ring-teal-400 transition-all"
            onChange={handleChange}
            onKeyDown={handleKeyDown}
          />
        </div>

        {/* PASSWORD */}
        <div className="relative mb-4">
          <span className="material-symbols-outlined absolute left-3 top-3 text-gray-400">
            lock
          </span>
          <input
            name="password"
            type="password"
            placeholder="Password"
            className="w-full pl-10 pr-3 py-3 rounded-xl bg-white/70 border border-gray-200 
                       focus:outline-none focus:ring-2 focus:ring-teal-400 transition-all"
            onChange={handleChange}
            onKeyDown={handleKeyDown}
          />
        </div>

        {/* CONFIRM */}
        <div className="relative mb-6">
          <span className="material-symbols-outlined absolute left-3 top-3 text-gray-400">
            verified_user
          </span>
          <input
            name="confirm"
            type="password"
            placeholder="Confirm Password"
            className="w-full pl-10 pr-3 py-3 rounded-xl bg-white/70 border border-gray-200 
                       focus:outline-none focus:ring-2 focus:ring-teal-400 transition-all"
            onChange={handleChange}
            onKeyDown={handleKeyDown}
          />
        </div>

        {/* BUTTON */}
        <button
          onClick={handleRegister}
          disabled={loading}
          className="w-full bg-gradient-to-r from-teal-600 to-cyan-500 text-white py-3 rounded-xl shadow-lg
                     hover:scale-105 active:scale-95 transition-all duration-200
                     disabled:opacity-50"
        >
          {loading ? "Creating account..." : "Register"}
        </button>

        {/* FOOTER */}
        <p className="text-sm text-center mt-6 text-gray-500">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-teal-600 font-medium hover:underline"
          >
            Login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}