import { useEffect, useRef, useState } from "react";

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8006/ws/events";

/**
 * WebSocket client hook used by the Dashboard to connect to the
 * realtime-service and maintain the latest event per sensor.
 *
 * It assumes the server sends UnifiedEvent payloads:
 * { event_id, sensor_id, type, value, timestamp }
 */
export function useWebSocketClient() {
  const [status, setStatus] = useState("disconnected");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sensors, setSensors] = useState({});
  const [history, setHistory] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    setStatus("connecting");
    const socket = new WebSocket(DEFAULT_WS_URL);
    socketRef.current = socket;

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("error");

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (!payload || typeof payload.sensor_id !== "string") {
          return;
        }

        setSensors((prev) => ({
          ...prev,
          [payload.sensor_id]: payload,
        }));
        setLastUpdated(payload.timestamp || new Date().toISOString());

        // Maintain a short history per sensor for basic trend charts.
        setHistory((prev) => {
          const existing = prev[payload.sensor_id] || [];
          const next = [...existing, payload].slice(-50);
          return { ...prev, [payload.sensor_id]: next };
        });
      } catch {
        // Ignore malformed messages.
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  return { status, sensors, history, lastUpdated };
}
