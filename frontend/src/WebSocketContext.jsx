import React, { createContext, useContext } from "react";
import { useWebSocketClient } from "./services/websocket.js";

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
  const ws = useWebSocketClient();
  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return ctx;
}

