import { useEffect, useRef, useState } from "react";

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8006/ws/events";

/**
 * WebSocket client hook used by Dashboard and Actuators pages to connect to the
 * realtime-service and maintain the latest event per sensor/actuator.
 *
 * It assumes the server sends UnifiedEvent payloads:
 * { event_id, sensor_id, type, value, timestamp }
 * OR actuator state events:
 * { event_id, actuator_id, state, timestamp }
 */
export function useWebSocketClient() {
  const [status, setStatus] = useState("disconnected");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sensors, setSensors] = useState({});
  const [actuatorStates, setActuatorStates] = useState({});
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
        
        // Handle sensor events
        if (payload && typeof payload.sensor_id === "string") {
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
        }
        
        // Handle actuator events
        if (payload && typeof payload.actuator_id === "string") {
          setActuatorStates((prev) => ({
            ...prev,
            [payload.actuator_id]: payload.state || "OFF",
          }));
          setLastUpdated(payload.timestamp || new Date().toISOString());
        }
      } catch {
        // Ignore malformed messages.
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  return { status, sensors, actuatorStates, history, lastUpdated };
}
