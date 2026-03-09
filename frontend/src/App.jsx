import React, { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Telemetry from "./pages/Telemetry.jsx";
import Rules from "./pages/Rules.jsx";
import Actuators from "./pages/Actuators.jsx";

const TABS = [
  { id: "dashboard", label: "Sensor Dashboard" },
  { id: "telemetry", label: "Telemetry" },
  { id: "rules", label: "Automation Rules" },
  { id: "actuators", label: "Actuators" },
];

function App() {
  const [page, setPage] = useState("dashboard");

  const renderPage = () => {
    if (page === "telemetry") return <Telemetry />;
    if (page === "rules") return <Rules />;
    if (page === "actuators") return <Actuators />;
    return <Dashboard />;
  };

  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        backgroundColor: "#f5f7fb",
        minHeight: "100vh",
      }}
    >
      <header
        style={{
          borderBottom: "1px solid #e2e8f0",
          backgroundColor: "#ffffff",
          padding: "0.75rem 2rem",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
            gap: "1rem",
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "1.4rem",
                fontWeight: 600,
              }}
            >
              Habitat Monitoring System
            </h1>
          </div>

          <nav
            aria-label="Main navigation"
            style={{
              display: "flex",
              gap: "0.25rem",
              backgroundColor: "#edf2f7",
              borderRadius: "999px",
              padding: "0.15rem",
            }}
          >
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setPage(tab.id)}
                style={{
                  border: "none",
                  backgroundColor:
                    page === tab.id ? "#ffffff" : "transparent",
                  color: page === tab.id ? "#2b6cb0" : "#4a5568",
                  padding: "0.35rem 0.9rem",
                  borderRadius: "999px",
                  fontSize: "0.85rem",
                  fontWeight: page === tab.id ? 600 : 500,
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main
        style={{
          maxWidth: "1200px",
          margin: "1.5rem auto 2rem",
          padding: "0 2rem",
        }}
      >
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
