# Mars Habitat Automation Platform

## System Overview

The Mars Habitat Automation Platform is a distributed software system designed to monitor and control the environmental conditions of a simulated Mars habitat. The system interacts with a heterogeneous Internet of Things (IoT) environment provided by the Mars IoT simulator, which exposes multiple sensors and actuators through different communication mechanisms.

The simulator produces environmental and telemetry data that describe the internal state of the habitat. These measurements include environmental indicators such as temperature, humidity, pressure, air quality, radiation levels, and subsystem telemetry such as power consumption or life-support metrics.

The simulator exposes data using two main mechanisms:

- **REST sensors**, which must be periodically queried using HTTP requests
- **Telemetry streams**, which continuously publish measurements asynchronously through message topics

Because these devices produce heterogeneous payloads and schemas, the platform introduces a **data normalization layer** that converts all incoming data into a standardized internal event format.

Once normalized, events are published to a message broker (**Kafka**) that acts as the backbone of the system's **event-driven architecture**. This architecture enables asynchronous communication between independent services and allows the system to scale and evolve more easily.

---

## Dashboard

A web-based dashboard provides a graphical interface that allows the habitat operator to:

- monitor environmental sensor values
- observe telemetry streams
- visualize system metrics in charts
- inspect actuator states
- manually control actuators
- create and manage automation rules

Through this dashboard, operators can supervise the habitat in real time and configure automated responses to environmental changes.

---

## User Stories

### Monitoring

1) As a Habitat Operator, I want to see the latest value of each sensor, so that I can monitor the current conditions inside the habitat.

2) As a Habitat Operator, I want sensor values to update automatically in real time, so that I can continuously monitor the habitat without refreshing the page.

3) As a Habitat Operator, I want to see the measurement unit of each sensor value, so that I can correctly interpret the data.

4) As a Habitat Operator, I want to see the name of each sensor, so that I can easily identify the device producing the data.

5) As a Habitat Operator, I want to see the timestamp of the latest sensor update, so that I can know how recent the displayed data is.

6) As a Habitat Operator, I want to monitor telemetry streams from habitat subsystems, so that I can observe continuously updated system metrics.

7) As a Habitat Operator, I want the dashboard to automatically receive telemetry data from streaming topics, so that telemetry metrics are updated in real time.

8) As a Habitat Operator, I want to visualize telemetry data such as power systems, radiation levels, and life support metrics, so that I can monitor critical habitat subsystems.

9) As a Habitat Operator, I want to visualize sensor and telemetry data in charts, so that I can observe trends while monitoring the system.

10) As a Habitat Operator, I want to see environmental indicators such as temperature, humidity, pressure, and air quality, so that I can ensure the habitat remains safe.

---

### Automation Rules

11) As a Habitat Operator, I want to create automation rules based on sensor values, so that the system can automatically react to dangerous conditions.

12) As a Habitat Operator, I want to define threshold conditions for sensors, so that actions are triggered when specific limits are exceeded.

13) As a Habitat Operator, I want to select which actuator should respond to a rule, so that the correct device is activated.

14) As a Habitat Operator, I want to enable or disable automation rules, so that I can control when automation is active.

15) As a Habitat Operator, I want to delete automation rules, so that I can remove rules that are no longer needed.

16) As a Habitat Operator, I want to see the list of all automation rules, so that I can understand the current automation logic of the system.

17) As a Habitat Operator, I want to see the condition and the action defined in each rule, so that I know how the system will react to sensor events.

18) As a Habitat Operator, I want all automation rules associated with an actuator to be automatically disabled when I manually control that actuator, so that my manual command is not immediately overridden by the automation engine.

---

### Actuator Monitoring and Alerts

19) As a Habitat Operator, I want to see the current state of each actuator, so that I know which devices are currently active in the habitat.

20) As a Habitat Operator, I want to receive alerts when sensor values exceed safe thresholds, so that I can intervene quickly if necessary.

---

## Unified Event Schema

Sensors and telemetry devices in the Mars IoT simulator generate heterogeneous data formats depending on the device type and communication protocol.

For example:

- REST sensors return structured JSON responses when queried via HTTP.
- Telemetry devices publish asynchronous messages through streaming topics.

In order to decouple internal services from device-specific schemas, the system converts all incoming payloads into a standardized event representation.

Each normalized event represents a snapshot of measurements produced by a single device at a given point in time and is published to the message broker so that all other services can process it uniformly.

This approach enables:

- consistent event processing across all services
- simplified rule evaluation
- easier integration of new device types
- loose coupling between services

### Normalized Event Fields

| Field | Type | Description |
|---|---|---|
| `event_id` | `string` | Unique identifier of the event (UUID) |
| `source_type` | `string` | Origin of the event: `"rest"` for polled sensors, `"telemetry"` for streaming topics |
| `source_id` | `string` | Identifier of the sensor or telemetry topic that produced the event |
| `schema_family` | `string` | Schema category describing the structure of the metrics (e.g., `rest.scalar.v1`, `topic.power.v1`) |
| `timestamp` | `string` | ISO 8601 timestamp of when the measurement was produced |
| `metrics` | `array` | List of one or more measurements included in the event (see Metric model below) |
| `status` | `string` (optional) | Status of the device or data validity (e.g., `"ok"`, `"warning"`) |
| `state_label` | `string` (optional) | Human-readable state label for discrete-state devices such as the airlock |

### Metric Model

Each element in the `metrics` array represents a single measurement:

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Name of the measurement (e.g., `"temperature"`, `"power"`, `"pm25"`) |
| `value` | `number` | Numeric measurement value |
| `unit` | `string` | Unit of measurement (e.g., `"°C"`, `"kW"`, `"ug/m3"`) |

### Example Normalized Events

**Single-metric REST sensor (temperature):**

```json
{
  "event_id": "e7f3c2a1-...",
  "source_type": "rest",
  "source_id": "greenhouse_temperature",
  "schema_family": "rest.scalar.v1",
  "timestamp": "2036-03-05T12:00:00Z",
  "metrics": [
    { "name": "temperature", "value": 27.5, "unit": "°C" }
  ],
  "status": "ok"
}
```

**Multi-metric telemetry sensor (power bus):**

```json
{
  "event_id": "b9d1f4e2-...",
  "source_type": "telemetry",
  "source_id": "power_bus",
  "schema_family": "topic.power.v1",
  "timestamp": "2036-03-05T12:00:01Z",
  "metrics": [
    { "name": "power",      "value": 3.2,   "unit": "kW"  },
    { "name": "voltage",    "value": 220.0, "unit": "V"   },
    { "name": "current",    "value": 14.5,  "unit": "A"   },
    { "name": "cumulative", "value": 102.7, "unit": "kWh" }
  ],
  "status": "ok"
}
```

**Airlock telemetry with state label:**

```json
{
  "event_id": "c3a7d9b0-...",
  "source_type": "telemetry",
  "source_id": "airlock-1",
  "schema_family": "topic.airlock.v1",
  "timestamp": "2036-03-05T12:00:02Z",
  "metrics": [
    { "name": "cycles_per_hour", "value": 4.0, "unit": "cycles/h" }
  ],
  "state_label": "IDLE",
  "status": "ok"
}
```


---

## Automation Rule Model

The platform supports automation rules that allow the system to automatically react to environmental changes detected by sensors.

Rules are defined by the habitat operator through the dashboard and are evaluated every time a new sensor event is received by the automation engine.

Each rule follows a simple **IF–THEN** structure:

```
IF <source_id> <operator> <threshold_value> [unit]
THEN set <actuator_name> to ON | OFF
```

### Supported Operators

The system supports the following comparison operators:

- `<`
- `<=`
- `=`
- `>`
- `>=`

### Example Rule

```
IF greenhouse_temperature > 28 °C
THEN set cooling_fan to ON
```

> **Note on manual control:** When an operator manually controls an actuator through the dashboard, all automation rules targeting that actuator are automatically disabled. This prevents the automation engine from immediately overriding the operator's manual command.

---

### Rule Evaluation Workflow

When a new sensor event arrives:

1. The event is consumed from the **message broker**.
2. The **Actuator Rules Service** retrieves all enabled rules associated with the corresponding `source_id`.
3. Each rule condition is evaluated against the first metric value of the event.
4. If the condition is satisfied, a command is sent to the **Actuator Management Service**.
5. The actuator state is updated through the simulator.

---

### Internal Rule Representation

Rules are stored in a persistent database using the following model:

| Field | Type | Description |
|---|---|---|
| `rule_id` | `string` | Unique identifier of the rule |
| `source_id` | `string` | Identifier of the sensor monitored by the rule (matches `source_id` in the unified event) |
| `operator` | `string` | Comparison operator (`<`, `<=`, `=`, `>`, `>=`) |
| `threshold_value` | `number` | Value used for the comparison |
| `unit` | `string` | Measurement unit used in the rule condition |
| `actuator_name` | `string` | Identifier of the target actuator |
| `action` | `string` | Desired actuator state: `"ON"` or `"OFF"` |
| `enabled` | `boolean` | Indicates whether the rule is currently active |

### Example Rule (JSON)

```json
{
  "rule_id": "rule-01",
  "source_id": "greenhouse_temperature",
  "operator": ">",
  "threshold_value": 28,
  "unit": "°C",
  "actuator_name": "cooling_fan",
  "action": "ON",
  "enabled": true
}
```

Rules are stored in a persistent database to ensure they remain available even after system restarts.

The rule engine continuously evaluates incoming events against active rules, enabling the platform to automatically react to changes in habitat conditions and maintain a safe environment for the simulated Mars habitat.

### Rule Mutual Exclusion

Only one rule may actively control a given actuator at any time. When a new rule is created targeting an actuator, all other existing rules targeting that same actuator are automatically disabled. This prevents conflicting commands from being issued to the same device simultaneously.
