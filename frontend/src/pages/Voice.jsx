/**
 * VOICE PAGE — HWELLBEING (FINAL PRODUCTION SAFE — NO ERRORS)
 */

import { useState, useRef, useEffect } from "react";
import { Mic, StopCircle } from "lucide-react";
import { motion } from "framer-motion";

import useStore from "../store/useStore";
import { createVoiceSocket } from "../api/api";

export default function Voice() {
  const {
    session_id,
    setSession,
    initSession,
    setError,
    error,
    setVoice, // ✅ REQUIRED
  } = useStore();

  const [listening, setListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("idle");

  const wsRef = useRef(null);
  const wsReadyRef = useRef(false);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);
  const chatRef = useRef(null);

  // =========================
  // INIT SESSION
  // =========================
  useEffect(() => {
    if (!session_id) initSession();
  }, [session_id, initSession]);

  // =========================
  // AUTO SCROLL
  // =========================
  useEffect(() => {
    try {
      if (chatRef.current) {
        chatRef.current.scrollTo({
          top: chatRef.current.scrollHeight,
          behavior: "smooth",
        });
      }
    } catch (err) {
      console.error("Scroll error:", err);
    }
  }, [messages]);

  // =========================
  // CLEANUP
  // =========================
  useEffect(() => {
    return () => {
      try {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
        }

        if (audioRef.current) {
          audioRef.current.pause();
        }

        if (wsRef.current) {
          wsRef.current.close();
        }
      } catch (err) {
        console.error("Cleanup error:", err);
      }
    };
  }, []);

  // =========================
  // WAIT WS
  // =========================
  const waitForWS = async () => {
    return new Promise((resolve) => {
      let attempts = 0;

      const check = () => {
        if (wsReadyRef.current === true) {
          resolve(true);
          return;
        }

        attempts++;

        if (attempts > 50) {
          console.error("WebSocket timeout");
          setError("Voice connection timeout");
          resolve(false);
          return;
        }

        setTimeout(check, 100);
      };

      check();
    });
  };

  // =========================
  // INIT WS
  // =========================
  const initWS = () => {
    if (wsRef.current) return;

    try {
      const ws = createVoiceSocket();

      if (!ws) {
        setError("Unable to establish voice connection");
        return;
      }

      ws.onopen = () => {
        wsReadyRef.current = true;

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "Hello 👋 Tell me your symptoms to begin.",
          },
        ]);
      };

      ws.onmessage = (event) => {
        let data = null;

        try {
          data = JSON.parse(event.data);
        } catch (err) {
          console.error("Invalid WS JSON:", err);
          setError("Invalid server response");
          return;
        }

        if (!data) return;

        try {
          if (data.session_id) {
            setSession(data.session_id);
          }

          if (data.type === "transcript") {
            setStatus("responding");

            setMessages((prev) => [
              ...prev,
              { role: "user", text: data.text || "" },
            ]);
          }

          if (data.type === "stream") {
            setStatus("responding");

            setMessages((prev) => {
              if (!prev.length) {
                return [{ role: "assistant", text: data.text || "" }];
              }

              const last = prev[prev.length - 1];

              if (last && last.role === "assistant") {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...last,
                    text: (last.text || "") + (data.text || ""),
                  },
                ];
              }

              return [...prev, { role: "assistant", text: data.text || "" }];
            });
          }

          if (data.type === "end") {
            setStatus("idle");

            const finalText = data.text || "";

            setMessages((prev) => [
              ...prev,
              { role: "assistant", text: finalText },
            ]);

            // ✅ CRITICAL FIX (Dashboard sync)
            if (finalText) {
              setVoice({
                last_message: finalText,
              });
            }

            if (data.audio_b64) {
              try {
                // ✅ stop previous audio
                if (audioRef.current) {
                  audioRef.current.pause();
                  audioRef.current = null;
                }

                const audio = new Audio(
                  `data:audio/mp3;base64,${data.audio_b64}`
                );

                audioRef.current = audio;

                audio.play().catch((err) => {
                  console.error("Audio play error:", err);
                  setError("Audio playback failed");
                });

              } catch (err) {
                console.error("Audio creation error:", err);
                setError("Audio initialization failed");
              }
            }
          }

        } catch (err) {
          console.error("WS processing error:", err);
          setError("Error processing response");
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setError("Voice connection error");
        wsReadyRef.current = false;
      };

      ws.onclose = () => {
        wsRef.current = null;
        wsReadyRef.current = false;
      };

      wsRef.current = ws;

    } catch (err) {
      console.error("WS init error:", err);
      setError("WebSocket initialization failed");
    }
  };

  // =========================
  // START LISTENING
  // =========================
  const startListening = async () => {
    if (listening) return;

    try {
      initWS();

      const ready = await waitForWS();
      if (!ready) return;

      setStatus("listening");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e && e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        try {
          setStatus("analyzing");

          const blob = new Blob(chunksRef.current || []);

          if (!blob || blob.size === 0) {
            console.warn("Empty audio blob");
            return;
          }

          const reader = new FileReader();

          reader.onloadend = () => {
            try {
              const base64 = reader.result?.split(",")[1];

              if (!base64) {
                console.error("Invalid base64 audio");
                return;
              }

              if (wsRef.current) {
                wsRef.current.send(
                  JSON.stringify({ audio_b64: base64 })
                );
              }

            } catch (err) {
              console.error("Audio send error:", err);
              setError("Failed to send audio");
            }
          };

          reader.readAsDataURL(blob);

        } catch (err) {
          console.error("Audio processing error:", err);
          setError("Audio processing failed");
        }

        setListening(false);
      };

      recorder.start();
      setListening(true);

      setTimeout(() => {
        try {
          if (recorder.state !== "inactive") {
            recorder.stop();
          }
        } catch (err) {
          console.error("Recorder stop error:", err);
        }
      }, 8000);

    } catch (err) {
      console.error("Mic error:", err);
      setError("Microphone access failed");
    }
  };

  const stopListening = () => {
    try {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }

    } catch (err) {
      console.error("Stop listening error:", err);
    }

    setListening(false);
    setStatus("idle");
  };

  return (
    <div className="h-full flex flex-col px-6 py-6">

      <h2 className="text-2xl font-semibold mb-4">Voice Assistant</h2>

      {error ? (
        <div className="bg-red-100 text-red-600 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      ) : null}

      <div
        ref={chatRef}
        className="flex-1 overflow-y-auto space-y-3 bg-gray-50 p-4 rounded-xl"
      >
        {messages.length === 0 ? (
          <p className="text-gray-400 text-center mt-10">
            Tap the mic and start speaking your symptoms...
          </p>
        ) : null}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-[75%] px-4 py-3 rounded-xl text-sm shadow ${
              msg.role === "user"
                ? "bg-teal-600 text-white ml-auto"
                : "bg-white border border-gray-200"
            }`}
          >
            <div className="whitespace-pre-line leading-relaxed">
              {msg.text || ""}
            </div>
          </div>
        ))}

        {status === "responding" ? (
          <div className="bg-white px-4 py-2 rounded-xl w-fit text-gray-500 text-sm shadow-sm">
            typing...
          </div>
        ) : null}
      </div>

      <div className="mt-6 flex flex-col items-center gap-2">
        <motion.button
          onClick={listening ? stopListening : startListening}
          animate={
            listening
              ? {
                  scale: [1, 1.2, 1],
                  boxShadow: ["0 0 0px", "0 0 30px", "0 0 0px"],
                }
              : {}
          }
          transition={{ repeat: Infinity, duration: 1 }}
          className={`w-20 h-20 rounded-full flex items-center justify-center text-white shadow-xl ${
            listening ? "bg-red-500" : "bg-teal-600"
          }`}
        >
          {listening ? <StopCircle size={30} /> : <Mic size={30} />}
        </motion.button>

        <p className="text-sm text-gray-500">
          {status === "listening"
            ? "Listening..."
            : status === "analyzing"
            ? "Analyzing..."
            : status === "responding"
            ? "Responding..."
            : "Tap to speak"}
        </p>
      </div>
    </div>
  );
}