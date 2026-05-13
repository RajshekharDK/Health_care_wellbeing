/**
 * APP — HWELLBEING (FINAL STABLE ROUTING — HOME ALWAYS ACCESSIBLE)
 */

import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";

import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Voice from "./pages/Voice";
import Triage from "./pages/Triage";
import Skin from "./pages/Skin";
import Login from "./pages/Login";
import Register from "./pages/Register";

import useUserLocation from "./hooks/useLocation";
import useStore from "./store/useStore";

// ==========================
// PRIVATE ROUTE
// ==========================
function PrivateRoute({ children }) {
  const token = useStore((s) => s.token);
  const hydrated = useStore((s) => s.hydrated);

  if (!hydrated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (!token) return <Navigate to="/login" replace />;

  return children;
}

// ==========================
// PUBLIC ROUTE
// ==========================
function PublicRoute({ children }) {
  const token = useStore((s) => s.token);
  if (token) return <Navigate to="/dashboard" replace />;
  return children;
}

// ==========================
// ROUTES
// ==========================
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <div className="flex-1 overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          className="h-full overflow-y-auto px-6 py-4"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -15 }}
          transition={{ duration: 0.25 }}
        >
          <Routes>
            {/* PUBLIC */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

            {/* PROTECTED */}
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/triage" element={<PrivateRoute><Triage /></PrivateRoute>} />
            <Route path="/skin" element={<PrivateRoute><Skin /></PrivateRoute>} />
            <Route path="/voice" element={<PrivateRoute><Voice /></PrivateRoute>} />

            {/* FALLBACK */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ==========================
// MAIN APP
// ==========================
export default function App() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // 🔐 HYDRATION
  useEffect(() => {
    const token = localStorage.getItem("token");

    useStore.setState({
      token: token || null,
      hydrated: true,
    });
  }, []);

  // 📍 LOCATION
  useUserLocation();

  // Prevent scroll when sidebar open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "auto";
  }, [open]);

  // ==========================
  // LAYOUT CONTROL
  // ==========================
  const hideLayout =
    location.pathname === "/" ||
    location.pathname.startsWith("/login") ||
    location.pathname.startsWith("/register");

  // ==========================
  // PUBLIC LAYOUT (HOME + AUTH)
  // ==========================
  if (hideLayout) {
    return <AnimatedRoutes />;
  }

  // ==========================
  // DASHBOARD LAYOUT
  // ==========================
  return (
    <div className="flex h-screen overflow-hidden bg-[#f7f9fb] dark:bg-gray-900">
      <Sidebar open={open} setOpen={setOpen} />

      <div className="flex-1 flex flex-col">
        <Header setOpen={setOpen} />
        <AnimatedRoutes />
      </div>
    </div>
  );
}