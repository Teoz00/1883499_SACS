import React, { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, apiPut } from "../services/api.js";
import { useWebSocketClient } from "../services/websocket.js";

// Actuators provided by the simulator.
const ACTUATORS = [
  { id: "cooling_fan", label: "Cooling Fan" },
  { id: "entrance_humidifier", label: "Entrance Humidifier" },
  { id: "hall_ventilation", label: "Hall Ventilation" },
  { id: "habitat_heater", label: "Habitat Heater" },
];

function Actuators() {
  const [states, setStates] = useState(
    /** @type {Record<string, "ON" | "OFF">} */ ({})
  );
  const [cachedStates, setCachedStates] = useState({});
  const [log, setLog] = useState([]);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState({});
  const [info, setInfo] = useState(null);

  // Use WebSocket for real-time actuator state updates
  const manualOverrideTime = React.useRef({});
  const { status: wsStatus, actuatorStates, setActuatorStates, lastUpdated } = useWebSocketClient(manualOverrideTime);

  // Merge WebSocket states with local state and cached state (manual commands take precedence)
  const mergedStates = { ...cachedStates, ...actuatorStates, ...states };

  // Load cached actuator data on component mount and tab visibility
  useEffect(() => {
    let cancelled = false;

    async function loadStates() {
      try {
        console.log("Loading actuator states from /api/actuators...");
        // Load initial states from actuator management service
        const data = await apiGet("/api/actuators");
        console.log("Received actuator states:", data);
        if (cancelled || !data || !Array.isArray(data.actuators)) return;
        const nextStates = {};
        for (const item of data.actuators) {
          if (!item || typeof item.id !== "string") continue;
          const state =
            typeof item.state === "string" && item.state.toUpperCase() === "ON"
              ? "ON"
              : "OFF";
          nextStates[item.id] = state;
        }
        if (!cancelled) {
          console.log("Setting initial actuator states:", nextStates);
          setStates(nextStates);
        }
      } catch (err) {
        // Non-fatal: keep previous states, but surface an error once.
        console.error("Failed to load actuator states", err);
        if (!cancelled) {
          setError(
            "Failed to refresh actuator states from simulator. Last known values are shown."
          );
        }
      }

      // Load cached states from realtime service
      try {
        console.log("Loading cached actuators from /api/actuators/latest...");
        const cacheData = await apiGet("/api/actuators/latest");
        console.log("Received actuator cache data:", cacheData);
        if (!cancelled && cacheData && cacheData.actuators) {
          // Extract just the state values from cache objects
          const extractedStates = {};
          Object.keys(cacheData.actuators).forEach(actuatorId => {
            const actuatorData = cacheData.actuators[actuatorId];
            extractedStates[actuatorId] = actuatorData.state || "OFF";
          });
          console.log("Setting cached actuator states:", extractedStates);
          setCachedStates(extractedStates);
        } else {
          console.log("No actuator cache data available");
        }
      } catch (err) {
        console.warn("Failed to load cached actuator data:", err);
      }
    }

    // Load initial states
    loadStates();

    // Reload when page becomes visible (tab switch)
    const handleVisibilityChange = () => {
      console.log("Actuators visibility changed, hidden:", document.hidden);
      if (!document.hidden) {
        console.log("Actuators page became visible, reloading cache...");
        loadStates();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);

    
    return () => { 
      cancelled = true; 
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const sortedLog = useMemo(
    () => [...log].sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1)),
    [log]
  );

  const sendCommand = async (actuatorId, command) => {
    setError(null);
    setInfo(null);
    setPending((prev) => ({ ...prev, [actuatorId]: true }));
    try {
      await apiPost(`/api/actuators/${actuatorId}`, { state: command });
      
      // Update ALL state sources immediately for instant UI feedback
      const now = Date.now();
      manualOverrideTime.current[actuatorId] = now;
      setTimeout(() => {
        delete manualOverrideTime.current[actuatorId];
      }, 5000);
      setStates((prev) => ({ ...prev, [actuatorId]: command }));
      setCachedStates((prev) => ({ ...prev, [actuatorId]: command }));
      setActuatorStates((prev) => ({ ...prev, [actuatorId]: command }));
      
      setLog((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${actuatorId}-${command}`,
          timestamp: new Date().toISOString(),
          actuatorId,
          rule: "Manual",
          action: `Turned ${command}`,
        },
      ]);

      // When manually toggling an actuator, temporarily disable all
      // rules that affect this actuator (run in background to avoid UI delay)
      setTimeout(async () => {
        try {
          const allRules = await apiGet("/api/rules");
          if (Array.isArray(allRules) && allRules.length > 0) {
            const affected = allRules.filter(
              (r) =>
                typeof r.action === "string" &&
                r.action.toLowerCase().includes(actuatorId.toLowerCase())
            );
            if (affected.length > 0) {
              await Promise.all(
                affected.map((rule) =>
                  apiPut(`/api/rules/${rule.id}`, {
                    name: rule.name,
                    condition: rule.condition,
                    action: rule.action,
                    enabled: false,
                  })
                )
              );
              setInfo(
                `Temporarily disabled ${affected.length} rule(s) affecting ${actuatorId}.`
              );
            }
          }
        } catch (err) {
          console.error("Failed to disable rules for actuator", actuatorId, err);
          // Non-fatal: actuator command still went through.
        }
      }, 100); // Small delay to not block the UI
    } catch (err) {
      console.error(err);
      setError("Failed to send actuator command.");
    } finally {
      setPending((prev) => ({ ...prev, [actuatorId]: false }));
    }
  };

  return (
    <section>
      <header
        style={{
          marginBottom: "1rem",
          backgroundColor: "#e6fffa",
          borderRadius: "0.5rem",
          padding: "0.75rem 1rem",
          border: "1px solid #81e6d9",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Actuators</h2>
      </header>

      {error && (
        <p style={{ fontSize: "0.8rem", color: "#c53030", marginTop: 0 }}>
          {error}
        </p>
      )}
      {info && (
        <p style={{ fontSize: "0.8rem", color: "#2f855a", marginTop: 0 }}>
          {info}
        </p>
      )}

      <section
        aria-label="Actuator states"
        style={{ marginBottom: "1.5rem" }}
      >
        <h3
          style={{
            fontSize: "1rem",
            margin: "0 0 0.5rem",
          }}
        >
          Actuator States
        </h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {ACTUATORS.map((a) => {
            const state = mergedStates[a.id] || "OFF";
            const isOn = state === "ON";
            const isBusy = pending[a.id];

            return (
              <article
                key={a.id}
                style={{
                  borderRadius: "0.5rem",
                  border: "1px solid #e2e8f0",
                  backgroundColor: "#ffffff",
                  padding: "0.75rem 1rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.35rem",
                  }}
                >
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "0.95rem",
                    }}
                  >
                    {a.label}
                  </h4>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      padding: "0.1rem 0.5rem",
                      borderRadius: "999px",
                      backgroundColor: isOn ? "#48bb78" : "#a0aec0",
                      color: "#ffffff",
                      fontWeight: 600,
                    }}
                  >
                    {state}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    type="button"
                    onClick={() => sendCommand(a.id, "OFF")}
                    disabled={isBusy || !isOn}
                    style={{
                      flex: 1,
                      border: "none",
                      borderRadius: "0.25rem",
                      padding: "0.3rem 0.5rem",
                      backgroundColor: isOn ? "#e53e3e" : "#edf2f7",
                      color: isOn ? "#ffffff" : "#4a5568",
                      fontSize: "0.8rem",
                      cursor: isOn && !isBusy ? "pointer" : "default",
                    }}
                  >
                    Turn OFF
                  </button>
                  <button
                    type="button"
                    onClick={() => sendCommand(a.id, "ON")}
                    disabled={isBusy || isOn}
                    style={{
                      flex: 1,
                      border: "none",
                      borderRadius: "0.25rem",
                      padding: "0.3rem 0.5rem",
                      backgroundColor: !isOn ? "#38a169" : "#edf2f7",
                      color: !isOn ? "#ffffff" : "#4a5568",
                      fontSize: "0.8rem",
                      cursor: !isOn && !isBusy ? "pointer" : "default",
                    }}
                  >
                    Turn ON
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section aria-label="Trigger log">
        <h3
          style={{
            fontSize: "1rem",
            margin: "0 0 0.5rem",
          }}
        >
          Trigger Log
        </h3>
        <div
          style={{
            borderRadius: "0.5rem",
            border: "1px solid #e2e8f0",
            backgroundColor: "#ffffff",
            padding: "0.75rem 1rem",
            fontSize: "0.8rem",
          }}
        >
          {sortedLog.length === 0 ? (
            <p style={{ margin: 0, color: "#4a5568" }}>
              Automatic and manual trigger events will appear here as you
              exercise the system.
            </p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr
                  style={{
                    textAlign: "left",
                    borderBottom: "1px solid #e2e8f0",
                  }}
                >
                  <th style={{ padding: "0.25rem 0.25rem" }}>Timestamp</th>
                  <th style={{ padding: "0.25rem 0.25rem" }}>Actuator</th>
                  <th style={{ padding: "0.25rem 0.25rem" }}>Rule</th>
                  <th style={{ padding: "0.25rem 0.25rem" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedLog.map((entry) => (
                  <tr
                    key={entry.id}
                    style={{
                      borderBottom: "1px solid #edf2f7",
                    }}
                  >
                    <td style={{ padding: "0.25rem 0.25rem" }}>
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: "0.25rem 0.25rem" }}>
                      {entry.actuatorId}
                    </td>
                    <td style={{ padding: "0.25rem 0.25rem" }}>
                      {entry.rule}
                    </td>
                    <td style={{ padding: "0.25rem 0.25rem" }}>
                      {entry.action}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </section>
  );
}

export default Actuators;
