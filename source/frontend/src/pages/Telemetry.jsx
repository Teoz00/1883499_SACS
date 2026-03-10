import React, { useMemo, useEffect, useState } from "react";
import { useWebSocketClient } from "../services/websocket.js";
import { apiGet } from "../services/api.js";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Known telemetry sources and how we present them.
const TELEMETRY_SOURCES = [
  {
    id: "solar_array",
    label: "Solar Array",
    unitLabel: "kW",
  },
  {
    id: "power_bus",
    label: "Power Bus",
    unitLabel: "kW",
  },
  {
    id: "power_consumption",
    label: "Power Consumption",
    unitLabel: "kW",
  },
  {
    id: "thermal_loop",
    label: "Thermal Loop",
    unitLabel: "°C",
  },
  {
    id: "airlock-1",
    label: "Airlock",
    unitLabel: "cycles/h",
  },
  {
    id: "radiation",
    label: "Radiation",
    unitLabel: "µSv/h",
  },
  {
    id: "life_support",
    label: "Life Support",
    unitLabel: "Status",
  },
];

function Telemetry() {
  const { sensors: wsSensors, history, lastUpdated } = useWebSocketClient();
  const [cachedSensors, setCachedSensors] = useState({});

  // Load cached sensor data on component mount and tab visibility change (exact same as Dashboard)
  useEffect(() => {
    let cancelled = false;
    
    const loadCache = async (retryOnEmpty = true) => {
      try {
        const response = await apiGet("/api/sensors/latest");
        const sensors = response?.sensors || {};
        
        if (Object.keys(sensors).length === 0 && retryOnEmpty) {
          setTimeout(() => loadCache(false), 2000);
          return;
        }
        
        if (!cancelled) {
          setCachedSensors(sensors);
        }
      } catch (err) {
        console.warn("Failed to load cached sensor data for telemetry:", err);
      }
    };
    
    loadCache();
    
    // Reload when page becomes visible (tab switch)
    const handleVisibilityChange = () => {
      console.log("Telemetry visibility changed, hidden:", document.hidden);
      if (!document.hidden) {
        console.log("Telemetry page became visible, reloading cache...");
        loadCache(false); // No retry on tab switch
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => { 
      cancelled = true; 
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Merge WebSocket data with cached data (WebSocket takes precedence) - exact same as Dashboard
  const latestById = useMemo(() => {
    const merged = { ...cachedSensors };
    Object.keys(wsSensors).forEach(sourceId => {
      merged[sourceId] = wsSensors[sourceId];
    });
    return merged;
  }, [cachedSensors, wsSensors]);

  return (
    <section>
      <header
        style={{
          marginBottom: "1rem",
          backgroundColor: "#ebf8ff",
          borderRadius: "0.5rem",
          padding: "0.75rem 1rem",
          border: "1px solid #bee3f8",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Telemetry</h2>
      </header>

      <div
        style={{
          marginBottom: "0.75rem",
          fontSize: "0.8rem",
          color: "#4a5568",
          display: "flex",
          justifyContent: "space-between",
          gap: "0.5rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <strong>Last Update:</strong>{" "}
          {lastUpdated ? new Date(lastUpdated).toLocaleString() : "–"}
        </div>
      </div>

      <section aria-label="Current telemetry values">
        <h3
          style={{
            fontSize: "1rem",
            margin: "0 0 0.5rem",
          }}
        >
          Current Telemetry Values
        </h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {TELEMETRY_SOURCES.map((meta) => {
            const evt = latestById[meta.id];
            
            // Determine if we have data
            const hasData = evt && evt.metrics && Array.isArray(evt.metrics) && evt.metrics.length > 0;
            const isLive = hasData;
            
            // Extract primary metric for chart
            const primaryMetric = evt?.metrics?.[0];
            const primaryValue = primaryMetric?.value;
            const primaryUnit = primaryMetric?.unit || meta.unitLabel;
            
            // Filter history for chart data
            const series = (history[meta.id] || []).filter(
              (e) => e && e.metrics && Array.isArray(e.metrics) && 
                     e.metrics.length > 0 && 
                     typeof e.metrics[0].value === "number"
            );
            const chartData = series.map((e, idx) => ({
              index: idx,
              value: e.metrics[0]?.value,
              timestamp: e.timestamp,
            }));

            return (
              <article
                key={meta.id}
                style={{
                  borderRadius: "0.5rem",
                  border: "1px solid #e2e8f0",
                  backgroundColor: "#ffffff",
                  padding: "0.75rem 1rem",
                  boxShadow:
                    "0 1px 2px rgba(0, 0, 0, 0.02), 0 0 0 1px rgba(226, 232, 240, 0.3)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    marginBottom: "0.5rem",
                  }}
                >
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "0.95rem",
                      fontWeight: 600,
                    }}
                  >
                    {meta.label}
                  </h4>
                  <div style={{ display: "flex", gap: "0.25rem", alignItems: "center" }}>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "999px",
                        backgroundColor: isLive ? "#10b981" : "#6b7280",
                        color: "white",
                        fontWeight: 600,
                      }}
                    >
                      {isLive ? "LIVE" : "WAITING"}
                    </span>
                    {evt && evt.status === "warning" && (
                      <span
                        style={{
                          fontSize: "0.6rem",
                          padding: "0.1rem 0.4rem",
                          borderRadius: "999px",
                          backgroundColor: "#fed7d7",
                          color: "#9c4221",
                          fontWeight: 600,
                        }}
                      >
                        ⚠️ WARNING
                      </span>
                    )}
                  </div>
                </div>
                
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "#374151",
                    lineHeight: "1.4",
                  }}
                >
                <p
                  style={{
                    margin: "0 0 0.5rem 0",
                    fontSize: "1.4rem",
                    fontWeight: 600,
                  }}
                >
                  {primaryValue !== undefined && primaryValue !== null ? primaryValue.toFixed(2) : "–"}{" "}
                  <span
                    style={{
                      fontSize: "0.8rem",
                      fontWeight: 400,
                      color: "#4a5568",
                    }}
                  >
                    {primaryUnit}
                  </span>
                </p>
                
                {/* Chart for primary metric */}
                {chartData.length > 1 ? (
                  <div style={{ width: "100%", height: 120, marginBottom: "0.5rem" }}>
                    <ResponsiveContainer>
                      <LineChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                        <XAxis
                          dataKey="index"
                          tick={false}
                          axisLine={false}
                          label={{ value: "", position: "insideBottom" }}
                        />
                        <YAxis
                          tick={{ fontSize: 10 }}
                          width={30}
                          stroke="#a0aec0"
                        />
                        <Tooltip
                          formatter={(val) => [
                            `${val.toFixed(2)} ${primaryUnit}`,
                            "Value",
                          ]}
                          labelFormatter={(index) => {
                            const item = chartData[index];
                            return item?.timestamp
                              ? new Date(item.timestamp).toLocaleString()
                              : "";
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#38a169"
                          strokeWidth={2}
                          dot={false}
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div style={{ marginBottom: "0.5rem", fontSize: "0.7rem", color: "#9ca3af" }}>
                    Waiting for chart data...
                  </div>
                )}
                
                {/* Secondary metrics list */}
                {hasData && evt.metrics.length > 1 && (
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#374151",
                      lineHeight: "1.4",
                      borderTop: "1px solid #e2e8f0",
                      paddingTop: "0.5rem",
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    {evt.metrics.slice(1).map((m, index) => (
                      <div key={m.name || index} style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{m.name}</span>
                        <span>{m.value.toFixed(2)} {m.unit}</span>
                      </div>
                    ))}
                    {evt.state_label && (
                      <div style={{ fontWeight: 600, marginTop: "0.2rem", display: "flex", justifyContent: "space-between" }}>
                        <span>state</span>
                        <span>{evt.state_label}</span>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Single metric case - show state_label if present */}
                {hasData && evt.metrics.length === 1 && evt.state_label && (
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#374151",
                      fontWeight: 600,
                      borderTop: "1px solid #e2e8f0",
                      paddingTop: "0.5rem",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>state</span>
                    <span>{evt.state_label}</span>
                  </div>
                )}
                
                {/* No data case */}
                {!hasData && (
                  <div style={{ color: "#9ca3af", fontStyle: "italic" }}>
                    No data yet
                  </div>
                )}
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </section>
  );
}

export default Telemetry;

