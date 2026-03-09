import React, { useMemo } from "react";
import { useWebSocketClient } from "../services/websocket.js";

// Known sensors exposed by the simulator and their presentation metadata.
const KNOWN_SENSORS = [
  {
    id: "greenhouse_temperature",
    label: "Greenhouse Temperature",
    unitLabel: "°C",
    preferredMetric: "temperature",
    threshold: 28,
  },
  {
    id: "entrance_humidity",
    label: "Entrance Humidity",
    unitLabel: "% RH",
    preferredMetric: "humidity",
    threshold: 70,
  },
  {
    id: "co2_hall",
    label: "CO₂ – Hall",
    unitLabel: "ppm",
    preferredMetric: "co2",
    threshold: 1000,
  },
  {
    id: "hydroponic_ph",
    label: "Hydroponic pH",
    unitLabel: "pH",
    preferredMetric: "ph",
    threshold: 7.5,
  },
  {
    id: "water_tank_level",
    label: "Water Tank Level",
    unitLabel: "% full",
    preferredMetric: "level_pct",
    threshold: 20,
  },
  {
    id: "corridor_pressure",
    label: "Corridor Pressure",
    unitLabel: "kPa",
    preferredMetric: "pressure",
    threshold: 110,
  },
  {
    id: "air_quality_pm25",
    label: "Air Quality – PM2.5",
    unitLabel: "µg/m³",
    preferredMetric: "pm25_ug_m3",
    threshold: 35,
  },
  {
    id: "air_quality_voc",
    label: "Air Quality – VOC",
    unitLabel: "ppm",
    preferredMetric: "voc",
    threshold: 800,
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
  const {
    status: wsStatus,
    sensors: wsSensors,
    history,
    lastUpdated: wsLastUpdated,
  } = useWebSocketClient();
  const lastUpdate = wsLastUpdated;

  // Build a map of latest readings by sensor id from the WebSocket stream.
  const latestById = useMemo(() => ({ ...wsSensors }), [wsSensors]);

  const alerts = KNOWN_SENSORS.filter((meta) => {
    const evt = latestById[meta.id];
    if (!evt) return false;
    if (evt.status && typeof evt.status === "string") {
      return evt.status.toLowerCase() === "warning";
    }
    const value = typeof evt.value === "number" ? evt.value : undefined;
    return value !== undefined && value > meta.threshold;
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
        <h2 style={{ marginTop: 0, marginBottom: "0.35rem" }}>
          Sensor Dashboard
        </h2>
        <p style={{ margin: 0, fontSize: "0.8rem", color: "#4a5568" }}>
          Live sensor values from the greenhouse simulator. Data is streamed in
          real time and periodically refreshed from the simulator.
        </p>
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
        <div>
          <strong>WebSocket:</strong> {wsStatus}
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
                  <strong>{meta.label}</strong> threshold exceeded:{" "}
                  {evt?.value} {meta.unitLabel} (limit {meta.threshold}{" "}
                  {meta.unitLabel})
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
            const isAlert = value !== undefined && value > meta.threshold;

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
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.75rem",
          }}
        >
          {KNOWN_SENSORS.map((meta) => {
            const series = history[meta.id] || [];
            const values = series
              .map((e) => (typeof e.value === "number" ? e.value : null))
              .filter((v) => v !== null);

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
                  {values.length > 0 && (
                    <span>
                      Latest: {values[values.length - 1]?.toFixed(1)}{" "}
                      {meta.unitLabel}
                    </span>
                  )}
                </div>
                <svg
                  viewBox="0 0 100 40"
                  role="img"
                  aria-label={`Trend for ${meta.label}`}
                  style={{ width: "100%", height: "70px" }}
                >
                  {values.length > 1 && (() => {
                    const min = Math.min(...values);
                    const max = Math.max(...values);
                    const span = max - min || 1;
                    const points = values.map((v, idx) => {
                      const x = (idx / Math.max(values.length - 1, 1)) * 100;
                      const y = 35 - ((v - min) / span) * 30;
                      return `${x},${y}`;
                    });
                    return (
                      <polyline
                        fill="none"
                        stroke="#3182ce"
                        strokeWidth="1.5"
                        points={points.join(" ")}
                      />
                    );
                  })()}
                </svg>
              </div>
            );
          })}
        </div>
      </section>
    </section>
  );
}

export default Dashboard;
