/**
 * DASHBOARD — HWELLBEING (FINAL + DOCTOR FILTER ADDED)
 */

import {
  Shield,
  Brain,
  AlertTriangle,
} from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import useStore from "../store/useStore";
import { healthAPI, doctorAPI } from "../api/api";

export default function Dashboard() {
  const { lastTriage, lastSkin, lastVoice, location } = useStore();
  const navigate = useNavigate();

  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const [doctors, setDoctors] = useState([]);
  const [loadingDoctors, setLoadingDoctors] = useState(false);
  const [doctorError, setDoctorError] = useState(null);

  // ✅ NEW: distance filter
  const [distanceRange, setDistanceRange] = useState([2, 20]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await healthAPI();
        setHealth(res);
      } catch {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
  }, []);

  useEffect(() => {
    const fetchDoctors = async () => {
      if (!location || typeof location.lat !== "number" || typeof location.lon !== "number") {
        return;
      }

      try {
        setLoadingDoctors(true);
        setDoctorError(null);

        const res = await doctorAPI(location.lat, location.lon);

        if (res?.available && Array.isArray(res.doctors)) {
          setDoctors(res.doctors);
        } else {
          setDoctors([]);
        }

      } catch (err) {
        setDoctorError(err?.message || "Failed to fetch doctors");
      } finally {
        setLoadingDoctors(false);
      }
    };

    fetchDoctors();
  }, [location]);

  // ✅ FILTER LOGIC
  const filteredDoctors = doctors.filter((doc) => {
    if (!doc?.distance_km) return false;

    return (
      doc.distance_km >= distanceRange[0] &&
      doc.distance_km <= distanceRange[1]
    );
  });

  const formatConfidence = (val) =>
    (Math.max(0, Math.min(1, Number(val || 0))) * 100).toFixed(2);

  const getRiskStyle = (risk) =>
    risk === "high"
      ? "text-red-500"
      : risk === "medium"
      ? "text-yellow-500"
      : "text-green-500";

  const topDisease = lastTriage?.[0];

  const voicePreview =
    lastVoice?.last_message?.length > 60
      ? lastVoice.last_message.slice(0, 60) + "..."
      : lastVoice?.last_message || "No voice interaction";

  const aiSummary = () => {
    if (!topDisease && !lastSkin && !lastVoice)
      return "No analysis yet. Start with symptom checker, skin scan, or voice assistant.";

    let summary = "";

    if (topDisease) summary += `Based on symptoms, possible condition: ${topDisease.disease}. `;
    if (lastSkin) summary += `Skin analysis suggests ${lastSkin.condition}. `;
    if (lastVoice) summary += `Voice interaction captured additional symptoms. `;

    return summary + "Please consult a medical professional.";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="px-6 md:px-10 py-8 space-y-10"
    >

      {/* HERO */}
      <div className="bg-teal-600 text-white p-6 rounded-3xl flex justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Brain size={20} />
            AI Health Engine
          </h2>
          <p className="text-sm mt-1">
            Your AI-powered health assistant
          </p>
        </div>

        <button
          onClick={() => navigate("/triage")}
          className="bg-white text-teal-700 px-5 py-2 rounded-full text-sm"
        >
          Start
        </button>
      </div>

      {/* SYSTEM */}
      <section className="grid lg:grid-cols-12 gap-6">

        <div className="lg:col-span-4 bg-white p-6 rounded-3xl border">
          <div className="flex justify-between mb-4">
            <span className="text-xs text-gray-400 uppercase">
              System Status
            </span>
            <Shield className="text-teal-600" />
          </div>

          <div className="text-xl font-bold">
            {loading ? "Checking..." : health?.status || "DOWN"}
          </div>

          <p className="text-sm text-gray-500">
            {health?.models_loaded ? "Models Ready" : "Loading..."}
          </p>
        </div>

        <div className="lg:col-span-8 bg-white p-6 rounded-3xl border">
          <h2 className="text-lg font-semibold mb-3">Top Prediction</h2>

          {topDisease ? (
            <>
              <div className="flex justify-between">
                <p className="text-xl font-bold">{topDisease.disease}</p>
                <div className="text-right">
                  <p className="text-teal-600">
                    {formatConfidence(topDisease.confidence)}%
                  </p>
                  <p className={getRiskStyle(topDisease.risk)}>
                    {topDisease.risk}
                  </p>
                </div>
              </div>

              <p className="text-sm text-gray-500 mt-2">
                {topDisease.explanation}
              </p>
            </>
          ) : (
            <p className="text-gray-400">No analysis yet</p>
          )}
        </div>
      </section>

      {/* AI SUMMARY */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">
          AI Summary
        </h3>
        <div className="bg-white p-5 rounded-xl border text-sm text-gray-600">
          {aiSummary()}
        </div>
      </section>

      {/* VOICE */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">
          Voice Insight
        </h3>
        <div className="bg-white p-5 rounded-xl border text-sm text-gray-500">
          {voicePreview}
        </div>
      </section>

      {/* DOCTORS */}
      <section>
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">
          Nearby Doctors
        </h3>

        {/* 🔥 SLIDER */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Distance</span>
            <span>{distanceRange[0]}km — {distanceRange[1]}km</span>
          </div>

          <input
            type="range"
            min="2"
            max="20"
            value={distanceRange[1]}
            onChange={(e) =>
              setDistanceRange([2, Number(e.target.value)])
            }
            className="w-full accent-teal-600"
          />
        </div>

        {!location && (
          <div className="bg-white p-5 rounded-xl border text-sm text-gray-500">
            Enable location to view doctors
          </div>
        )}

        {loadingDoctors && (
          <div className="bg-white p-5 rounded-xl border text-sm text-gray-500">
            Fetching doctors...
          </div>
        )}

        {doctorError && (
          <div className="bg-red-100 text-red-600 p-4 rounded-xl text-sm">
            {doctorError}
          </div>
        )}

        {!loadingDoctors && filteredDoctors.length === 0 && (
          <div className="bg-white p-5 rounded-xl border text-sm text-gray-500">
            No doctors in selected range
          </div>
        )}

        {filteredDoctors.length > 0 && (
          <div className="grid md:grid-cols-2 gap-4">
            {filteredDoctors.map((doc, i) => (
              <div key={i} className="bg-white p-5 rounded-xl border shadow-sm">
                <h4 className="font-semibold">{doc.name}</h4>
                <p className="text-sm text-gray-500">
                  {doc.type} • {doc.distance}
                </p>
                <button
                  onClick={() =>
                    window.open(
                      `https://www.google.com/maps?q=${doc.lat},${doc.lon}`,
                      "_blank"
                    )
                  }
                  className="text-teal-600 text-sm mt-2"
                >
                  Open in Maps →
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

    </motion.div>
  );
}