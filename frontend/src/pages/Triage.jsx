/**
 * TRIAGE PAGE — HWELLBEING (PRODUCTION FIXED + UI UPGRADED)
 */

import { useState } from "react";
import { Activity, Bolt, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

import { predictSymptomsAPI } from "../api/api";
import useStore from "../store/useStore";

export default function Triage() {
  const [input, setInput] = useState("");
  const [results, setResults] = useState([]);

  const { setTriage, setLoading, loading, setError, error } = useStore();

  // =========================
  // ANALYZE
  // =========================
  const analyze = async () => {
    if (!input.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const symptoms = input
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      if (!symptoms.length) {
        throw new Error("Please enter valid symptoms");
      }

      const data = await predictSymptomsAPI(symptoms);

      if (!Array.isArray(data)) {
        throw new Error("Invalid response from server");
      }

      setResults(data);
      setTriage(data);

    } catch (err) {
      console.error("TRIAGE ERROR:", err);

      let message = "Something went wrong";

      if (typeof err === "string") message = err;
      else if (err?.message) message = err.message;
      else if (err?.raw?.response?.data?.detail)
        message = err.raw.response.data.detail;
      else if (err?.raw?.message) message = err.raw.message;

      setError(message);

    } finally {
      setLoading(false);
    }
  };

  // =========================
  // ENTER KEY
  // =========================
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      analyze();
    }
  };

  // =========================
  // RISK STYLE
  // =========================
  const getRiskStyle = (risk) => {
    if (risk === "high") return "text-red-500";
    if (risk === "medium") return "text-yellow-500";
    return "text-green-500";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="px-6 md:px-10 py-8 space-y-10"
    >
      {/* HEADER */}
      <section className="space-y-4 max-w-3xl">
        <h2 className="text-3xl md:text-4xl font-bold">
          Symptom Assessment
        </h2>

        <p className="text-gray-500 dark:text-gray-400">
          Enter symptoms separated by commas (e.g., fever, cough, headache)
        </p>
      </section>

      {/* INPUT */}
      <motion.section className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl p-6 rounded-2xl border space-y-6">
        <textarea
          disabled={loading}
          className="w-full p-4 rounded-xl border outline-none text-sm disabled:opacity-60"
          placeholder="fever, cough, chest pain..."
          rows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <div className="flex justify-between items-center">
          <button
            onClick={() => {
              setInput("");
              setResults([]);
              setError(null);
            }}
            className="text-sm text-gray-400 hover:text-red-500"
          >
            Clear
          </button>

          <button
            onClick={analyze}
            disabled={loading}
            className="bg-teal-600 text-white px-6 py-2.5 rounded-full flex items-center gap-2 disabled:opacity-50"
          >
            <Bolt size={16} />
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </motion.section>

      {/* ERROR */}
      {error && (
        <p className="text-red-500 text-sm">{error}</p>
      )}

      {/* LOADING */}
      {loading && (
        <p className="text-gray-400 animate-pulse">
          Running AI triage...
        </p>
      )}

      {/* RESULTS */}
      {!loading && results.length > 0 && (
        <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((item, i) => {
            const confidence =
              Math.max(0, Math.min(1, Number(item?.confidence || 0))) * 100;

            const risk = item?.risk || "low";

            // ✅ CORRECT FIELD (FIXED)
            const prescription = item?.prescription || {};
            const meds = Array.isArray(prescription?.medications)
              ? prescription.medications
              : [];

            return (
              <div
                key={i}
                className={`bg-white dark:bg-gray-800 p-5 rounded-xl border shadow-sm space-y-3 ${
                  i === 0 ? "ring-2 ring-teal-500" : ""
                }`}
              >
                {/* HEADER */}
                <div className="flex justify-between">
                  <Activity className="text-teal-600" size={18} />

                  <div className="text-right">
                    <div className="text-sm font-semibold text-teal-600">
                      {confidence.toFixed(2)}%
                    </div>

                    <div className={`text-xs ${getRiskStyle(risk)}`}>
                      {risk.toUpperCase()}
                    </div>
                  </div>
                </div>

                {/* DISEASE */}
                <h4 className="font-semibold text-sm">
                  {item?.disease || "Unknown"}
                </h4>

                {/* EXPLANATION */}
                <p className="text-xs text-gray-500">
                  {item?.explanation || "No explanation available"}
                </p>

                {/* 💊 PRESCRIPTION */}
                {prescription?.available && meds.length > 0 ? (
                  <div className="text-xs mt-2">
                    <p className="font-medium">💊 Prescription:</p>

                    <ul className="list-disc ml-4 mt-1 space-y-1">
                      {meds.map((m, idx) => (
                        <li key={idx}>
                          <div>{m?.name || "Medicine"}</div>

                          {m?.instructions && (
                            <div className="text-gray-500 text-[11px]">
                              {m.instructions}
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="text-xs text-red-500 mt-2">
                    🚑 {prescription?.message || "No prescription available. Please consult a doctor."}
                  </div>
                )}

                {/* ALERT */}
                {risk === "high" && (
                  <div className="flex items-center gap-1 text-xs text-red-500">
                    <AlertTriangle size={14} />
                    Seek medical attention
                  </div>
                )}

                {/* BAR */}
                <div className="w-full h-2 bg-gray-100 rounded-full">
                  <div
                    className="h-full bg-teal-500"
                    style={{ width: `${confidence}%` }}
                  />
                </div>
              </div>
            );
          })}
        </section>
      )}

      {/* EMPTY */}
      {!loading && results.length === 0 && !error && (
        <div className="text-center text-gray-400 py-16">
          Enter symptoms to begin analysis
        </div>
      )}
    </motion.div>
  );
}