import { useEffect, useState } from "react";

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8006/ws/events";

/**
 * Minimal WebSocket client placeholder used by the Dashboard
 * to connect to the realtime-service.
 */
export function useWebSocketClient() {
  const [status, setStatus] = useState("disconnected");

  useEffect(() => {
    setStatus("connecting");
    const socket = new WebSocket(DEFAULT_WS_URL);

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("error");

    // In a full implementation, incoming messages would be processed here.
    // socket.onmessage = (event) => { ... };

    return () => {
      socket.close();
    };
  }, []);

  return { status };
}

