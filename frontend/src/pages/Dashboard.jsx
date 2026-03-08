import React from "react";
import { useWebSocketClient } from "../services/websocket.js";

function Dashboard() {
  const { status } = useWebSocketClient();

  return (
    <section>
      <h2>Dashboard</h2>
      <p>Realtime event stream and system status will appear here.</p>
      <p>WebSocket status: {status}</p>
    </section>
  );
}

export default Dashboard;

