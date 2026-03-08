import React, { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Rules from "./pages/Rules.jsx";
import Actuators from "./pages/Actuators.jsx";

function App() {
  const [page, setPage] = useState("dashboard");

  const renderPage = () => {
    if (page === "rules") return <Rules />;
    if (page === "actuators") return <Actuators />;
    return <Dashboard />;
  };

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "1rem" }}>
      <header style={{ marginBottom: "1rem" }}>
        <h1>IoT Event Processing Platform</h1>
        <nav style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
          <button onClick={() => setPage("dashboard")}>Dashboard</button>
          <button onClick={() => setPage("rules")}>Rules</button>
          <button onClick={() => setPage("actuators")}>Actuators</button>
        </nav>
      </header>
      <main>{renderPage()}</main>
    </div>
  );
}

export default App;

