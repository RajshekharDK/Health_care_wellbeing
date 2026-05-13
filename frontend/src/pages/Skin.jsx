/**
 * SKIN PAGE — HWELLBEING (PRODUCTION FIXED + UI HARDENED)
 */

import { useState, useRef, useEffect } from "react";
import { UploadCloud, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

import { predictSkinAPI } from "../api/api";
import useStore from "../store/useStore";

export default function Skin() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);

  const { setSkin, setLoading, loading, setError, error } = useStore();

  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  // =========================
  // FILE VALIDATION
  // =========================
  const handleFile = (f) => {
    if (!f) return;

    if (!["image/jpeg", "image/png"].includes(f.type)) {
      setError("Only JPG or PNG images allowed");
      return;
    }

    if (f.size > 5 * 1024 * 1024) {
      setError("File size must be under 5MB");
      return;
    }

    setError(null);

    if (preview) URL.revokeObjectURL(preview);

    const url = URL.createObjectURL(f);

    setFile(f);
    setPreview(url);
    setResult(null);
  };

  // =========================
  // ANALYZE
  // =========================
  const analyze = async () => {
    if (!file || loading) return;

    setLoading(true);
    setError(null);

    try {
      const data = await predictSkinAPI(file);

      if (!data || typeof data !== "object") {
        throw new Error("Invalid response from server");
      }

      setResult(data);
      setSkin(data);

    } catch (err) {
      console.error("SKIN ERROR:", err);

      let message = "Analysis failed";

      if (typeof err === "string") message = err;
      else if (err?.message) message = err.message;
      else if (err?.raw?.response?.data?.detail)
        message = err.raw.response.data.detail;
      else if (err?.raw?.message)
        message = err.raw.message;

      setError(message);

    } finally {
      setLoading(false);
    }
  };

  const removeFile = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  const confidence =
    Math.max(0, Math.min(1, Number(result?.confidence || 0))) * 100;

  // ✅ FIXED: USE prescription (NOT treatment)
  const prescription = result?.prescription || {};
  const meds = Array.isArray(prescription?.medications)
    ? prescription.medications
    : [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="px-6 md:px-10 py-8 space-y-10"
    >
      {/* HEADER */}
      <div className="max-w-3xl">
        <h2 className="text-3xl font-bold mb-3">Skin Analysis</h2>
        <p className="text-gray-500">
          Upload an image to detect skin condition using AI.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">

        {/* LEFT */}
        <div className="lg:col-span-7 space-y-6">
          <motion.div
            whileHover={{ scale: 1.01 }}
            onClick={() => inputRef.current?.click()}
            className="bg-white/70 p-8 rounded-2xl border-2 border-dashed text-center cursor-pointer"
          >
            {!preview ? (
              <>
                <UploadCloud className="mx-auto mb-4 text-teal-600" size={40} />
                <h3 className="font-semibold">Click to upload image</h3>
                <p className="text-sm text-gray-400">JPG / PNG (max 5MB)</p>
              </>
            ) : (
              <>
                <img
                  src={preview}
                  alt="preview"
                  className="mx-auto max-h-72 rounded-xl mb-4"
                />

                <div className="flex justify-center gap-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      analyze();
                    }}
                    className="bg-teal-600 text-white px-5 py-2 rounded-full"
                  >
                    {loading ? "Analyzing..." : "Analyze"}
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile();
                    }}
                    className="bg-gray-200 px-5 py-2 rounded-full"
                  >
                    Remove
                  </button>
                </div>
              </>
            )}

            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </motion.div>

          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}
        </div>

        {/* RIGHT */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-5 rounded-xl border space-y-4">
            <h3 className="font-semibold text-sm">Analysis Result</h3>

            {loading && (
              <p className="text-gray-400 animate-pulse">
                Processing image...
              </p>
            )}

            {!loading && result && (
              <>
                <p className="text-sm">
                  <strong>Condition:</strong>{" "}
                  {result?.condition || "Unknown"}
                </p>

                <p className="text-sm">
                  <strong>Severity:</strong>{" "}
                  {result?.severity || "N/A"}
                </p>

                <p className="text-sm">
                  <strong>Confidence:</strong>{" "}
                  {confidence.toFixed(2)}%
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
                  <p className="text-xs text-red-500">
                    🚑 {prescription?.message || "No prescription available. Please consult a doctor."}
                  </p>
                )}

                {/* BAR */}
                <div className="w-full h-2 bg-gray-100 rounded-full">
                  <div
                    className="h-full bg-teal-500"
                    style={{ width: `${confidence}%` }}
                  />
                </div>
              </>
            )}

            {!result && !loading && (
              <p className="text-gray-400 text-sm">
                Upload an image to begin analysis
              </p>
            )}
          </div>

          {/* LOW CONFIDENCE WARNING */}
          {result && confidence < 50 && (
            <div className="bg-red-100 p-4 rounded-xl flex gap-3 border">
              <AlertTriangle className="text-red-600" />
              <p className="text-xs">
                Low confidence result. Try a clearer image or consult a doctor.
              </p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}