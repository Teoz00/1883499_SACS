import React, { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../services/api.js";

const OPERATORS = ["<", "<=", "=", ">=", ">"];
const COMMANDS = ["ON", "OFF"];

const KNOWN_SENSORS = [
  "greenhouse_temperature",
  "entrance_humidity",
  "co2_hall",
  "hydroponic_ph",
  "water_tank_level",
  "corridor_pressure",
  "air_quality_pm25",
  "air_quality_voc",
];

const KNOWN_UNITS = ["°C", "% RH", "ppm", "pH", "% full", "kPa", "µg/m³"];

const KNOWN_ACTUATORS = [
  "cooling_fan",
  "entrance_humidifier",
  "hall_ventilation",
  "habitat_heater",
];

// Default mapping from sensor to its unit and preferred actuator.
const SENSOR_DEFAULTS = {
  greenhouse_temperature: { unit: "°C", actuator: "cooling_fan" },
  entrance_humidity: { unit: "% RH", actuator: "entrance_humidifier" },
  co2_hall: { unit: "ppm", actuator: "hall_ventilation" },
  hydroponic_ph: { unit: "pH", actuator: "habitat_heater" },
  water_tank_level: { unit: "% full", actuator: "habitat_heater" },
  corridor_pressure: { unit: "kPa", actuator: "hall_ventilation" },
  air_quality_pm25: { unit: "µg/m³", actuator: "hall_ventilation" },
  air_quality_voc: { unit: "ppm", actuator: "hall_ventilation" },
};

function buildCondition({ sensor, operator, threshold, unit, actuator, command }) {
  const trimmedUnit = (unit || "").trim();
  const unitPart = trimmedUnit ? ` ${trimmedUnit}` : "";
  return `IF ${sensor} ${operator} ${threshold}${unitPart} THEN set ${actuator} to ${command}`;
}

function buildAction({ actuator, command }) {
  return `THEN set ${actuator} to ${command}`;
}

function extractActuatorIdFromAction(action) {
  // Expected shapes:
  // "THEN set <actuator> to ON"
  // or full condition: "IF ... THEN set <actuator> to ON"
  if (typeof action !== "string") return null;
  const lower = action.toLowerCase();
  const marker = "then set ";
  const idx = lower.indexOf(marker);
  if (idx === -1) return null;
  const after = action.slice(idx + marker.length).trim();
  const [actuator] = after.split(/\s+/);
  return actuator || null;
}

function Rules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: "",
    sensor: "",
    operator: ">",
    threshold: "",
    unit: "",
    actuator: "",
    command: "ON",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadRules() {
      setLoading(true);
      try {
        const data = await apiGet("/api/rules");
        if (!cancelled) {
          setRules(Array.isArray(data) ? data : []);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError("Failed to load rules.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadRules();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreate = async (evt) => {
    evt.preventDefault();
    if (!form.name || !form.sensor || !form.threshold || !form.actuator) {
      setError("Please fill in rule name, sensor, threshold, and actuator.");
      return;
    }
    setSubmitting(true);
    try {
      const condition = buildCondition(form);
      const action = buildAction(form);
      const payload = {
        name: form.name,
        condition,
        action,
        enabled: true,
      };
      const created = await apiPost("/api/rules", payload);

      // Enforce that rules targeting the same actuator are mutually exclusive.
      const createdActuator = extractActuatorIdFromAction(created.action);
      let nextRules = [...rules, created];
      if (createdActuator) {
        const toDisable = nextRules.filter(
          (r) =>
            r.id !== created.id &&
            extractActuatorIdFromAction(r.action) === createdActuator &&
            r.enabled
        );
        if (toDisable.length > 0) {
          const updated = await Promise.all(
            toDisable.map((rule) =>
              apiPut(`/api/rules/${rule.id}`, {
                name: rule.name,
                condition: rule.condition,
                action: rule.action,
                enabled: false,
              })
            )
          );
          nextRules = nextRules.map((r) => {
            const match = updated.find((u) => u.id === r.id);
            return match || r;
          });
        }
      }

      setRules(nextRules);
      setForm({
        name: "",
        sensor: "",
        operator: form.operator,
        threshold: "",
        unit: "",
        actuator: "",
        command: form.command,
      });
      setCreating(false);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to create rule.");
    } finally {
      setSubmitting(false);
    }
  };

  const updateRuleEnabled = async (rule, enabled) => {
    try {
      const updated = await apiPut(`/api/rules/${rule.id}`, {
        name: rule.name,
        condition: rule.condition,
        action: rule.action,
        enabled,
      });
      let nextRules = rules.map((r) => (r.id === updated.id ? updated : r));

      // If we just ENABLED a rule, disable all other rules tied to the same actuator.
      if (enabled) {
        const actuator = extractActuatorIdFromAction(updated.action);
        if (actuator) {
          const toDisable = nextRules.filter(
            (r) =>
              r.id !== updated.id &&
              extractActuatorIdFromAction(r.action) === actuator &&
              r.enabled
          );
          if (toDisable.length > 0) {
            const disabled = await Promise.all(
              toDisable.map((r) =>
                apiPut(`/api/rules/${r.id}`, {
                  name: r.name,
                  condition: r.condition,
                  action: r.action,
                  enabled: false,
                })
              )
            );
            nextRules = nextRules.map((r) => {
              const match = disabled.find((d) => d.id === r.id);
              return match || r;
            });
          }
        }
      }

      setRules(nextRules);
    } catch (err) {
      console.error(err);
      setError("Failed to update rule.");
    }
  };

  const deleteRule = async (ruleId) => {
    try {
      await apiDelete(`/api/rules/${ruleId}`);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err) {
      console.error(err);
      setError("Failed to delete rule.");
    }
  };

  const sortedRules = useMemo(
    () => [...rules].sort((a, b) => a.name.localeCompare(b.name)),
    [rules]
  );

  return (
    <section>
      <header
        style={{
          marginBottom: "1rem",
          backgroundColor: "#fefcbf",
          borderRadius: "0.5rem",
          padding: "0.75rem 1rem",
          border: "1px solid #f6e05e",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Automation Rules</h2>
      </header>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.75rem",
          gap: "0.5rem",
          flexWrap: "wrap",
        }}
      >
        <h3
          style={{
            fontSize: "1rem",
            margin: 0,
          }}
        >
          All Rules
        </h3>
        <button
          type="button"
          onClick={() => setCreating((v) => !v)}
          style={{
            border: "none",
            borderRadius: "0.25rem",
            padding: "0.3rem 0.75rem",
            backgroundColor: creating ? "#e2e8f0" : "#3182ce",
            color: creating ? "#1a202c" : "#ffffff",
            fontSize: "0.8rem",
            cursor: "pointer",
          }}
        >
          {creating ? "Cancel" : "Create Rule"}
        </button>
      </div>

      {creating && (
        <form
          onSubmit={handleCreate}
          style={{
            marginBottom: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: "0.5rem",
            border: "1px solid #fefcbf",
            backgroundColor: "#fffff0",
            fontSize: "0.85rem",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: "0.5rem 0.75rem",
              marginBottom: "0.75rem",
            }}
          >
            <label>
              <div>Rule name</div>
              <input
                type="text"
                value={form.name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, name: e.target.value }))
                }
                style={{ width: "100%" }}
              />
            </label>

            <label>
              <div>Sensor</div>
              <select
                value={form.sensor}
                onChange={(e) => {
                  const sensor = e.target.value;
                  const defaults = SENSOR_DEFAULTS[sensor] || {};
                  setForm((f) => ({
                    ...f,
                    sensor,
                    unit: defaults.unit ?? f.unit,
                    actuator: defaults.actuator ?? f.actuator,
                  }));
                }}
                style={{ width: "100%" }}
              >
                <option value="">Select sensor…</option>
                {KNOWN_SENSORS.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div>Operator</div>
              <select
                value={form.operator}
                onChange={(e) =>
                  setForm((f) => ({ ...f, operator: e.target.value }))
                }
                style={{ width: "100%" }}
              >
                {OPERATORS.map((op) => (
                  <option key={op} value={op}>
                    {op}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div>Threshold</div>
              <input
                type="number"
                value={form.threshold}
                onChange={(e) =>
                  setForm((f) => ({ ...f, threshold: e.target.value }))
                }
                style={{ width: "100%" }}
              />
            </label>

            <label>
              <div>Unit (optional)</div>
              <select
                value={form.unit}
                onChange={(e) =>
                  setForm((f) => ({ ...f, unit: e.target.value }))
                }
                style={{ width: "100%" }}
              >
                <option value="">No unit</option>
                {KNOWN_UNITS.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div>Actuator</div>
              <select
                value={form.actuator}
                onChange={(e) =>
                  setForm((f) => ({ ...f, actuator: e.target.value }))
                }
                style={{ width: "100%" }}
              >
                <option value="">Select actuator…</option>
                {KNOWN_ACTUATORS.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div>Action</div>
              <select
                value={form.command}
                onChange={(e) =>
                  setForm((f) => ({ ...f, command: e.target.value }))
                }
                style={{ width: "100%" }}
              >
                {COMMANDS.map((cmd) => (
                  <option key={cmd} value={cmd}>
                    Turn {cmd}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              border: "none",
              borderRadius: "0.25rem",
              padding: "0.4rem 0.9rem",
              backgroundColor: "#3182ce",
              color: "#ffffff",
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            {submitting ? "Creating…" : "Create Rule"}
          </button>
        </form>
      )}

      {error && (
        <p style={{ fontSize: "0.8rem", color: "#c53030", marginTop: 0 }}>
          {error}
        </p>
      )}

      {loading && rules.length === 0 ? (
        <p style={{ fontSize: "0.85rem", color: "#4a5568" }}>
          Loading rules…
        </p>
      ) : sortedRules.length === 0 ? (
        <p style={{ fontSize: "0.85rem", color: "#4a5568" }}>
          No rules defined yet. Create your first rule to automate actuators.
        </p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: "0.5rem",
          }}
        >
          {sortedRules.map((rule) => (
            <article
              key={rule.id}
              style={{
                borderRadius: "0.5rem",
                border: rule.enabled
                  ? "1px solid #c6f6d5"
                  : "1px solid #e2e8f0",
                backgroundColor: rule.enabled ? "#f0fff4" : "#ffffff",
                padding: "0.6rem 0.9rem",
                display: "grid",
                gridTemplateColumns: "minmax(0, 1fr) auto",
                gap: "0.5rem 0.75rem",
                alignItems: "center",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    marginBottom: "0.25rem",
                  }}
                >
                  <strong>{rule.name}</strong>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      padding: "0.1rem 0.5rem",
                      borderRadius: "999px",
                      backgroundColor: rule.enabled ? "#48bb78" : "#a0aec0",
                      color: "#ffffff",
                      fontWeight: 600,
                    }}
                  >
                    {rule.enabled ? "ENABLED" : "DISABLED"}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#4a5568" }}>
                  <div>
                    <strong>Condition:</strong> {rule.condition}
                  </div>
                  <div>
                    <strong>Action:</strong> {rule.action}
                  </div>
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.25rem",
                  justifySelf: "end",
                }}
              >
                <button
                  type="button"
                  onClick={() => updateRuleEnabled(rule, !rule.enabled)}
                  style={{
                    border: "none",
                    borderRadius: "0.25rem",
                    padding: "0.25rem 0.6rem",
                    backgroundColor: rule.enabled ? "#edf2f7" : "#38a169",
                    color: rule.enabled ? "#1a202c" : "#ffffff",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                >
                  {rule.enabled ? "Disable" : "Enable"}
                </button>
                <button
                  type="button"
                  onClick={() => deleteRule(rule.id)}
                  style={{
                    border: "none",
                    borderRadius: "0.25rem",
                    padding: "0.25rem 0.6rem",
                    backgroundColor: "#e53e3e",
                    color: "#ffffff",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default Rules;
