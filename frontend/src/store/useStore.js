/**
 * GLOBAL STATE — HWELLBEING (FINAL PRODUCTION STABLE)
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

// =========================
// HELPERS
// =========================
const generateId = () =>
  `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

let errorTimer = null;

// =========================
// STORE
// =========================
const useStore = create(
  persist(
    (set, get) => ({
      // =========================
      // 🔐 AUTH
      // =========================
      token: null,
      hydrated: false,

      setHydrated: (val) => set({ hydrated: val }),

      initAuth: () => {
        const token = localStorage.getItem("token");

        if (!token || token === "undefined" || token === "null") {
          localStorage.removeItem("token");
          set({ token: null });
          return;
        }

        set({ token });
      },

      setToken: (data) => {
        if (!data) return;

        const token =
          typeof data === "string"
            ? data
            : data?.access_token || data?.token;

        if (!token) return;

        localStorage.setItem("token", token);
        set({ token });
      },

      logout: () => {
        localStorage.removeItem("token");

        set({
          token: null,
          session_id: null,
          lastTriage: null,
          lastSkin: null,
          lastVoice: null,
          voiceHistory: [],
          loading: false,
          error: null,
        });
      },

      // =========================
      // 🎤 SESSION
      // =========================
      session_id: null,

      initSession: () => {
        if (get().session_id) return;

        const id = generateId();
        set({ session_id: id });
      },

      setSession: (id) => set({ session_id: id }),

      clearSession: () =>
        set({
          session_id: null,
          lastVoice: null,
          voiceHistory: [],
        }),

      // =========================
      // 🧠 HEALTH DATA
      // =========================
      lastTriage: null,
      lastSkin: null,
      lastVoice: null,
      voiceHistory: [],

      setTriage: (data) => set({ lastTriage: data }),
      setSkin: (data) => set({ lastSkin: data }),

      // 🔥 VOICE HANDLER (SAFE + NORMALIZED)
      setVoice: (data) => {
        if (!data) return;

        const text =
          data?.last_message ||
          data?.text ||
          data?.response ||
          "";

        if (!text || typeof text !== "string") return;

        const normalized = {
          last_message: text,
          timestamp: Date.now(),
        };

        set((state) => ({
          lastVoice: normalized,
          voiceHistory: [...state.voiceHistory.slice(-9), normalized],
        }));
      },

      // =========================
      // 🌍 LOCATION
      // =========================
      location: null,
      locationAttempted: false,

      setLocation: (loc) => {
        if (!loc) return;
        set({ location: loc });
      },

      setLocationAttempted: (val) =>
        set({ locationAttempted: val }),

      // =========================
      // ⚙️ UI STATE
      // =========================
      loading: false,
      error: null,

      setLoading: (val) => set({ loading: val }),

      setError: (err) => {
        const message =
          typeof err === "string"
            ? err
            : err?.message || "Something went wrong";

        set({ error: message });

        if (errorTimer) clearTimeout(errorTimer);

        errorTimer = setTimeout(() => {
          set({ error: null });
        }, 3000);
      },

      clearError: () => {
        if (errorTimer) clearTimeout(errorTimer);
        set({ error: null });
      },
    }),
    {
      name: "hwellbeing-store",

      // 🔥 Persist only important data
      partialize: (state) => ({
        token: state.token,
        lastTriage: state.lastTriage,
        lastSkin: state.lastSkin,
        lastVoice: state.lastVoice,
        voiceHistory: state.voiceHistory,
        location: state.location,
      }),
    }
  )
);

export default useStore;