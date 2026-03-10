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

// Known sensors exposed by the simulator and their presentation metadata.
const KNOWN_SENSORS = [
  {
    id: "greenhouse_temperature",
    label: "Greenhouse Temperature",
    unitLabel: "°C",
    preferredMetric: "temperature",
  },
  {
    id: "entrance_humidity",
    label: "Entrance Humidity",
    unitLabel: "% RH",
    preferredMetric: "humidity",
  },
  {
    id: "co2_hall",
    label: "CO₂ – Hall",
    unitLabel: "ppm",
    preferredMetric: "co2",
  },
  {
    id: "hydroponic_ph",
    label: "Hydroponic pH",
    unitLabel: "pH",
    preferredMetric: "ph",
  },
  {
    id: "water_tank_level",
    label: "Water Tank Level",
    unitLabel: "% full",
    preferredMetric: "level_pct",
  },
  {
    id: "corridor_pressure",
    label: "Corridor Pressure",
    unitLabel: "kPa",
    preferredMetric: "pressure",
  },
  {
    id: "air_quality_pm25",
    label: "Air Quality – PM2.5",
    unitLabel: "µg/m³",
    preferredMetric: "pm25_ug_m3",
  },
  {
    id: "air_quality_voc",
    label: "Air Quality – VOC",
    unitLabel: "ppm",
    preferredMetric: "voc",
  },
];

function formatTimestamp(ts) {
  if (!ts) return "–";
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

function Dashboard() {
  const { sensors: wsSensors, history, lastUpdated: wsLastUpdated } =
    useWebSocketClient();
  const [cachedSensors, setCachedSensors] = useState({});
  const lastUpdate = wsLastUpdated;

  // Load cached sensor data on component mount and tab visibility change
  useEffect(() => {
    let cancelled = false;
    async function loadCachedSensors() {
      try {
        console.log("Loading cached sensors from /api/sensors/latest...");
        const data = await apiGet("/api/sensors/latest");
        console.log("Received cache data:", data);
        if (!cancelled && data && data.sensors) {
          console.log("Setting cached sensors:", data.sensors);
          setCachedSensors(data.sensors);
        } else {
          console.log("No cache data available");
        }
      } catch (err) {
        console.warn("Failed to load cached sensor data:", err);
      }
    }
    loadCachedSensors();
    
    // Reload when page becomes visible (tab switch)
    const handleVisibilityChange = () => {
      console.log("Visibility changed, hidden:", document.hidden);
      if (!document.hidden) {
        console.log("Page became visible, reloading cache...");
        loadCachedSensors();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => { 
      cancelled = true; 
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Merge WebSocket data with cached data (WebSocket takes precedence)
  const latestById = useMemo(() => {
    const merged = { ...cachedSensors };
    Object.keys(wsSensors).forEach(sensorId => {
      merged[sensorId] = wsSensors[sensorId];
    });
    return merged;
  }, [cachedSensors, wsSensors]);

  const alerts = KNOWN_SENSORS.filter((meta) => {
    const evt = latestById[meta.id];
    if (!evt) return false;
    if (evt.status && typeof evt.status === "string") {
      return evt.status.toLowerCase() === "warning";
    }
    return false;
  });

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
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Sensor Dashboard</h2>
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
          <strong>Last Update:</strong> {formatTimestamp(lastUpdate)}
        </div>
      </div>

      {alerts.length > 0 && (
        <div
          style={{
            borderRadius: "0.5rem",
            border: "1px solid #fed7d7",
            backgroundColor: "#fff5f5",
            padding: "0.75rem 1rem",
            marginBottom: "1rem",
            color: "#c53030",
            fontSize: "0.85rem",
          }}
        >
          <strong style={{ display: "block", marginBottom: "0.25rem" }}>
            Alerts
          </strong>
          <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
            {alerts.map((meta) => {
              const evt = latestById[meta.id];
              return (
                <li key={meta.id}>
                  <strong>{meta.label}</strong>: {evt?.value} {meta.unitLabel}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <section
        aria-label="Current sensor values"
        style={{ marginBottom: "1.5rem" }}
      >
        <h3
          style={{
            fontSize: "1rem",
            margin: "0 0 0.5rem",
          }}
        >
          Current Sensor Values
        </h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {KNOWN_SENSORS.map((meta) => {
            const evt = latestById[meta.id];
            const value =
              evt && typeof evt.value === "number"
                ? evt.value
                : undefined;
            const isAlert =
              evt &&
              typeof evt.status === "string" &&
              (evt.status.toLowerCase() === "warning" || evt.status.toLowerCase() === "critical");

            return (
              <article
                key={meta.id}
                style={{
                  borderRadius: "0.5rem",
                  border: `1px solid ${isAlert ? "#feb2b2" : "#e2e8f0"}`,
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
                    marginBottom: "0.35rem",
                  }}
                >
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "0.95rem",
                    }}
                  >
                    {meta.label}
                  </h4>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      padding: "0.1rem 0.4rem",
                      borderRadius: "999px",
                      backgroundColor: isAlert ? "#fed7d7" : "#e6fffa",
                      color: isAlert ? "#c53030" : "#2c7a7b",
                      fontWeight: 600,
                    }}
                  >
                    {value === undefined
                      ? "WAITING"
                      : isAlert
                      ? "ALERT"
                      : "OK"}
                  </span>
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: "1.4rem",
                    fontWeight: 600,
                  }}
                >
                  {value !== undefined ? value.toFixed(1) : "–"}{" "}
                  <span
                    style={{
                      fontSize: "0.8rem",
                      fontWeight: 400,
                      color: "#4a5568",
                    }}
                  >
                    {meta.unitLabel}
                  </span>
                </p>
              </article>
            );
          })}
        </div>
      </section>

      <section aria-label="Sensor trends">
        <h3
          style={{
            fontSize: "1rem",
            margin: "0 0 0.5rem",
          }}
        >
          Sensor Trends
        </h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {KNOWN_SENSORS.map((meta) => {
            const series = (history[meta.id] || []).filter(
              (e) => typeof e.value === "number"
            );
            const chartData = series.map((e, idx) => ({
              index: idx,
              value: e.value,
              timestamp: e.timestamp,
            }));

            return (
              <div
                key={meta.id}
                style={{
                  borderRadius: "0.5rem",
                  border: "1px solid #e2e8f0",
                  backgroundColor: "#ffffff",
                  padding: "0.75rem 1rem",
                  fontSize: "0.8rem",
                  color: "#4a5568",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    marginBottom: "0.25rem",
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{meta.label}</span>
                  {chartData.length > 0 && (
                    <span>
                      Latest:{" "}
                      {chartData[chartData.length - 1].value.toFixed(1)}{" "}
                      {meta.unitLabel}
                    </span>
                  )}
                </div>
                {chartData.length > 1 ? (
                  <div style={{ width: "100%", height: 120 }}>
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
                          formatter={(value) => [`${value.toFixed(2)} ${meta.unitLabel}`, "Value"]}
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
                          stroke="#3182ce"
                          strokeWidth={2}
                          dot={false}
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <p style={{ margin: "0.25rem 0 0" }}>
                    Waiting for enough data points to draw a trend.
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </section>
  );
}

export default Dashboard;
