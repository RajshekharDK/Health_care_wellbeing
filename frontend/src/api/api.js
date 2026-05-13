/**
 * API CLIENT — HWELLBEING (FINAL HARDENED + DOCTOR SAFE)
 */

import axios from "axios";
import useStore from "../store/useStore";

// ============================
// BASE URL
// ============================
const BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

// ============================
// 🔥 SAFE WS URL BUILDER
// ============================
const getWSBase = () => {
  try {
    const url = new URL(BASE_URL);
    const protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${url.host}`;
  } catch (err) {
    console.error("WS URL parse failed:", err);
    return BASE_URL.replace(/^http/, "ws");
  }
};

// ============================
// AXIOS INSTANCE
// ============================
const API = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000, // ✅ increased (critical)
  headers: {
    Accept: "application/json",
  },
});

// ============================
// 🔐 REQUEST INTERCEPTOR
// ============================
API.interceptors.request.use((config) => {
  const token = useStore.getState().token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// ============================
// ❌ RESPONSE INTERCEPTOR
// ============================
API.interceptors.response.use(
  (res) => res,
  (error) => {
    const store = useStore.getState();

    let message = "Network error";
    const status = error?.response?.status;
    const data = error?.response?.data;

    if (typeof data === "string") {
      message = data;
    } else if (data?.detail) {
      message = data.detail;
    } else if (data?.error) {
      message = data.error;
    } else if (error?.message) {
      message = error.message;
    }

    if (typeof message !== "string") {
      try {
        message = JSON.stringify(message);
      } catch {
        message = "Unexpected error occurred";
      }
    }

    if (status === 401) {
      store.logout();
      window.location.href = "/login";
    }

    console.error("API ERROR:", {
      message,
      status,
      url: error?.config?.url,
    });

    return Promise.reject({
      message,
      status,
      raw: error,
    });
  }
);

// ============================
// 🔐 AUTH
// ============================
export const loginAPI = async (username, password) => {
  const res = await API.post("/auth/login", { username, password });
  return res.data;
};

export const registerAPI = async (username, password) => {
  const res = await API.post("/auth/register", { username, password });
  return res.data;
};

// ============================
// ❤️ HEALTH
// ============================
export const healthAPI = async () => {
  const res = await API.get("/health");
  return res.data;
};

// ============================
// 🧠 TRIAGE
// ============================
export const predictSymptomsAPI = async (symptoms) => {
  const res = await API.post("/predict/symptoms", { symptoms });
  return res.data;
};

// ============================
// 🖼 SKIN
// ============================
export const predictSkinAPI = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await API.post("/predict/skin", formData);
  return res.data;
};

// ============================
// 🫁 LUNG
// ============================
export const predictLungAPI = async (features) => {
  const res = await API.post("/predict/lung", { features });
  return res.data;
};

// ============================
// 🎤 VOICE SOCKET
// ============================
export const createVoiceSocket = () => {
  const token = useStore.getState().token;

  if (!token) {
    console.warn("WS ERROR: No token available");
    return null;
  }

  const wsBase = getWSBase();
  const wsUrl = `${wsBase}/ws/voice?token=${encodeURIComponent(token)}`;

  try {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("WS OPEN");
    ws.onerror = (e) => console.error("WS ERROR:", e);
    ws.onclose = () => console.warn("WS CLOSED");

    return ws;
  } catch (err) {
    console.error("WS INIT FAILED:", err);
    return null;
  }
};

// ============================
// 🏥 DOCTORS (SAFE FALLBACK)
// ============================
export const doctorAPI = async (lat, lon) => {
  if (typeof lat !== "number" || typeof lon !== "number") {
    throw new Error("Invalid location");
  }

  try {
    const res = await API.post("/doctors", { lat, lon });
    return res.data;
  } catch (err) {
    // ✅ prevent dashboard crash
    console.warn("Doctor API fallback:", err?.message);

    return {
      available: false,
      confidence: 0,
      doctors: [],
      message: "Doctor service slow, try again",
    };
  }
};

export default API;