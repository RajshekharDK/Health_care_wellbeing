/**
 * CHAT PAGE — HWELLBEING (REPURPOSED)
 *
 * Purpose:
 * Text-based AI interaction using triage API
 * (stateless, no streaming)
 */

import { useState } from "react";
import { Send, User, Bot } from "lucide-react";
import { motion } from "framer-motion";

import { predictSymptomsAPI } from "../api/api";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // =========================
  // SEND MESSAGE
  // =========================
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMsg },
    ]);

    setInput("");
    setLoading(true);

    try {
      const symptoms = userMsg
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const data = await predictSymptomsAPI(symptoms);

      const reply =
        data?.[0]?.explanation ||
        "No clear diagnosis found.";

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: err },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full px-6 py-6">

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-10">
            Enter symptoms to start
          </p>
        )}

        {messages.map((msg, i) => (
          <motion.div key={i}>
            {msg.role === "ai" ? (
              <div className="bg-gray-100 p-3 rounded-xl max-w-xl">
                <Bot size={14} className="mb-1 text-teal-600" />
                {msg.text}
              </div>
            ) : (
              <div className="ml-auto bg-teal-600 text-white p-3 rounded-xl max-w-xl">
                <User size={14} className="mb-1" />
                {msg.text}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* INPUT */}
      <div className="mt-4 flex gap-2">
        <input
          className="flex-1 border rounded-full px-4 py-2"
          placeholder="Enter symptoms (comma separated)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />

        <button
          onClick={handleSend}
          disabled={loading}
          className="bg-teal-600 text-white p-3 rounded-full"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}