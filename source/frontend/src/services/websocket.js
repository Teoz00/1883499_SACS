import { useEffect, useRef, useState } from "react";

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8006/ws/events";
const DEFAULT_ACTUATOR_WS_URL =
  import.meta.env.VITE_ACTUATOR_WS_URL || "ws://localhost:8005/ws/actuators";

/**
 * WebSocket client hook used by Dashboard and Actuators pages to connect to the
 * realtime-service and maintain the latest event per sensor/actuator.
 *
 * It assumes the server sends UnifiedEvent payloads:
 * { event_id, sensor_id, type, value, timestamp }
 * OR actuator state events:
 * { event_id, actuator_id, state, timestamp }
 */
export function useWebSocketClient(manualOverrideTime = null) {
  const [status, setStatus] = useState("disconnected");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sensors, setSensors] = useState({});
  const [actuatorStates, setActuatorStates] = useState({});
  const [history, setHistory] = useState({});
  const sensorSocketRef = useRef(null);
  const actuatorSocketRef = useRef(null);

  useEffect(() => {
    // Connect to sensors WebSocket
    setStatus("connecting");
    const sensorSocket = new WebSocket(DEFAULT_WS_URL);
    sensorSocketRef.current = sensorSocket;

    sensorSocket.onopen = () => {
      console.log("Sensor WebSocket connected");
      if (actuatorSocketRef.current?.readyState === WebSocket.OPEN) {
        setStatus("connected");
      } else {
        setStatus("sensors-connected");
      }
    };
    sensorSocket.onclose = () => {
      console.log("Sensor WebSocket disconnected");
      if (actuatorSocketRef.current?.readyState === WebSocket.OPEN) {
        setStatus("actuators-connected");
      } else if (actuatorSocketRef.current?.readyState === WebSocket.CONNECTING) {
        setStatus("actuators-connecting");
      } else {
        setStatus("disconnected");
      }
    };
    sensorSocket.onerror = (error) => {
      console.error("Sensor WebSocket error:", error);
      setStatus("error");
    };

    sensorSocket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        // Handle sensor events (unified event schema)
        if (payload && typeof payload.source_id === "string") {
          // Store the complete unified event
          setSensors((prev) => ({
            ...prev,
            [payload.source_id]: payload,
          }));
          setLastUpdated(payload.timestamp || new Date().toISOString());

          // Maintain a short history per sensor for basic trend charts.
          setHistory((prev) => {
            const existing = prev[payload.source_id] || [];
            const next = [...existing, payload].slice(-50);
            return { ...prev, [payload.source_id]: next };
          });
        }
      } catch {
        // Ignore malformed messages.
      }
    };

    // Connect to actuators WebSocket
    const actuatorSocket = new WebSocket(DEFAULT_ACTUATOR_WS_URL);
    actuatorSocketRef.current = actuatorSocket;

    actuatorSocket.onopen = () => {
      console.log("Actuator WebSocket connected");
      if (sensorSocketRef.current?.readyState === WebSocket.OPEN) {
        setStatus("connected");
      } else {
        setStatus("actuators-connected");
      }
    };
    actuatorSocket.onclose = () => {
      console.log("Actuator WebSocket disconnected");
      if (sensorSocketRef.current?.readyState === WebSocket.OPEN) {
        setStatus("sensors-connected");
      } else if (sensorSocketRef.current?.readyState === WebSocket.CONNECTING) {
        setStatus("sensors-connecting");
      } else {
        setStatus("disconnected");
      }
    };
    actuatorSocket.onerror = (error) => {
      console.error("Actuator WebSocket error:", error);
      setStatus("error");
    };

    actuatorSocket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        // Handle actuator events
        if (payload && typeof payload.actuator_id === "string") {
          const overrideTs = manualOverrideTime?.current?.[payload.actuator_id];
          const eventTs = payload.timestamp ? new Date(payload.timestamp).getTime() : null;
          if (overrideTs && eventTs !== null && eventTs < overrideTs) return;
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
      sensorSocket.close();
      actuatorSocket.close();
      sensorSocketRef.current = null;
      actuatorSocketRef.current = null;
    };
  }, []);

  return { status, sensors, actuatorStates, setActuatorStates, history, lastUpdated };
}
