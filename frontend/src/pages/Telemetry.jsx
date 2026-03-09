import React, { useMemo } from "react";
import { useWebSocketClient } from "../services/websocket.js";
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
    label: "Solar Array Power",
    unitLabel: "kW",
    metricKey: "power_kw",
  },
  {
    id: "power_bus",
    label: "Power Bus",
    unitLabel: "kW",
    metricKey: "power_kw",
  },
  {
    id: "power_consumption",
    label: "Power Consumption",
    unitLabel: "kW",
    metricKey: "power_kw",
  },
  {
    id: "thermal_loop",
    label: "Thermal Loop Temperature",
    unitLabel: "°C",
    metricKey: "temperature_c",
  },
  {
    id: "airlock",
    label: "Airlock Cycles",
    unitLabel: "cycles/h",
    metricKey: "cycles_per_hour",
  },
];

function Telemetry() {
  const { sensors: wsSensors, history, lastUpdated } = useWebSocketClient();

  const latestById = useMemo(() => ({ ...wsSensors }), [wsSensors]);

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
            const value =
              evt && typeof evt.value === "number" ? evt.value : undefined;
            const series = (history[meta.id] || []).filter(
              (e) => typeof e.value === "number"
            );
            const chartData = series.map((e, idx) => ({
              index: idx,
              value: e.value,
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
                      backgroundColor: "#edf2f7",
                      color: "#4a5568",
                      fontWeight: 600,
                    }}
                  >
                    {value === undefined ? "WAITING" : "LIVE"}
                  </span>
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: "1.4rem",
                    fontWeight: 600,
                  }}
                >
                  {value !== undefined ? value.toFixed(2) : "–"}{" "}
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
                {chartData.length > 1 ? (
                  <div style={{ width: "100%", height: 120, marginTop: "0.5rem" }}>
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
                            `${val.toFixed(2)} ${meta.unitLabel}`,
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
                  <p style={{ margin: "0.5rem 0 0", fontSize: "0.75rem" }}>
                    Waiting for enough data points to draw a trend.
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </section>
    </section>
  );
}

export default Telemetry;

