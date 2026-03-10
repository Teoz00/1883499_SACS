# SYSTEM DESCRIPTION

The IoT Mars Habitat Platform is an event-driven microservices system designed to monitor and control a simulated Mars habitat greenhouse environment.

The system collects environmental sensor data and telemetry metrics from an IoT simulator, processes these events through a Kafka-based message bus, evaluates automation rules, and provides a real-time dashboard for habitat operators.

The platform enables operators to:
- Monitor environmental conditions (temperature, humidity, pressure, air quality)
- Monitor subsystem telemetry (power systems, radiation, life support)
- Visualize data trends through real-time charts
- Define automation rules based on sensor thresholds
- Automatically control actuators when conditions are met
- Manually override actuator states and disable conflicting rules

The architecture follows an **event-driven microservices design**, where all sensor data flows through Kafka topics before being consumed by downstream services and the frontend interface. Each service has a single, well-defined responsibility and communicates exclusively through Kafka or REST/WebSocket interfaces.

---

# USER STORIES

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

11) As a Habitat Operator, I want to create automation rules based on sensor values, so that the system can automatically react to dangerous conditions.

12) As a Habitat Operator, I want to define threshold conditions for sensors, so that actions are triggered when specific limits are exceeded.

13) As a Habitat Operator, I want to select which actuator should respond to a rule, so that the correct device is activated.

14) As a Habitat Operator, I want to enable or disable automation rules, so that I can control when automation is active.

15) As a Habitat Operator, I want to delete automation rules, so that I can remove rules that are no longer needed.

16) As a Habitat Operator, I want to see the list of all automation rules, so that I can understand the current automation logic of the system.

17) As a Habitat Operator, I want to see the condition and the action defined in each rule, so that I know how the system will react to sensor events.

18) As a Habitat Operator, I want to disable the rules of a certain actuator when it is manually turned on or off.

19) As a Habitat Operator, I want to see the current state of each actuator, so that I know which devices are currently active in the habitat.

20) As a Habitat Operator, I want to receive alerts when sensor values exceed safe thresholds, so that I can intervene quickly if necessary.

---

# CONTAINERS

## CONTAINER_NAME: ingestion-service

### DESCRIPTION

The ingestion-service is responsible for collecting all raw data from the IoT simulator and publishing it to Kafka.

It polls REST endpoints for environmental sensors every 3 seconds and connects to telemetry topics using Server-Sent Events (SSE). All collected data is published to Kafka as raw events with the full simulator payload preserved. The service does not transform or interpret data — it only forwards it downstream.

### USER STORIES

4, 5, 6, 7, 10

### PORTS

8001:8001

### PERSISTENCE EVALUATION

The ingestion-service does not require persistent storage. It only forwards raw events to Kafka and maintains no state.

### EXTERNAL SERVICES CONNECTIONS

- IoT Simulator (REST polling + SSE streaming)

### MICROSERVICES

#### MICROSERVICE: ingestion-service

- TYPE: backend
- PORTS: 8001
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - asyncio: manages concurrent polling and streaming tasks
    - aiokafka: async Kafka producer for publishing raw events
    - httpx: async HTTP client for REST polling and SSE stream connections
    - Uvicorn: ASGI server to serve the FastAPI application

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application factory, startup/shutdown lifecycle, background task management
    - `services/poller.py`: background loop that polls simulator REST endpoints every 3 seconds
    - `services/simulator_client.py`: HTTP client for simulator REST API, returns full raw payload per sensor
    - `services/telemetry_streams.py`: opens one SSE connection per telemetry topic, processes incoming events with exponential backoff on reconnect
    - `kafka/producer.py`: Kafka producer that publishes raw dicts to the `raw-sensor-events` topic

- ENDPOINTS:

  | HTTP METHOD | URL | Description | User Stories |
  | ----------- | --- | ----------- | ------------ |
  | GET | /health | Returns service health status | — |

- KAFKA TOPICS PRODUCED:

  | Topic | Description | User Stories |
  | ----- | ----------- | ------------ |
  | raw-sensor-events | Full simulator payload with sensor_id injected — both REST and SSE telemetry events | 4, 5, 6, 7, 10 |

  > **Note:** Both REST sensor events and SSE telemetry events are published to the same Kafka topic `raw-sensor-events`. There is no separate `raw-telemetry-events` topic.

---

## CONTAINER_NAME: processing-service

### DESCRIPTION

The processing-service transforms raw events from Kafka into the standardized **UnifiedEvent** schema used by all downstream services.

It reads raw simulator payloads, determines the schema family based on `sensor_id`, extracts the relevant fields, constructs a structured metrics array, and publishes a normalized UnifiedEvent to the `normalized-events` topic. It is the single source of truth for data normalization in the system.

### USER STORIES

1, 2, 3, 5, 6, 8, 9

### PORTS

8002:8002

### PERSISTENCE EVALUATION

The processing-service does not require persistent storage. It is a stateless transformation service.

### EXTERNAL SERVICES CONNECTIONS

The processing-service does not connect to external services.

### MICROSERVICES

#### MICROSERVICE: processing-service

- TYPE: backend
- PORTS: 8002
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - Pydantic: schema validation and definition of UnifiedEvent and Metric models
    - aiokafka: async Kafka consumer (raw-sensor-events) and producer (normalized-events)
    - asyncio: manages the background event processing loop

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, Kafka consumer initialization, background task
    - `services/event_processor.py`: Kafka consumer loop, forwards messages to transformer, publishes results
    - `services/event_transformer.py`: core normalization logic — maps sensor_id to schema family, builds metrics array from real simulator fields
    - `models/unified_event.py`: Pydantic models for UnifiedEvent and Metric

- SCHEMA FAMILY MAPPING:

  | sensor_id | schema_family | source_type |
  | --------- | ------------- | ----------- |
  | greenhouse_temperature | rest.scalar.v1 | rest |
  | entrance_humidity | rest.scalar.v1 | rest |
  | co2_hall | rest.scalar.v1 | rest |
  | corridor_pressure | rest.scalar.v1 | rest |
  | hydroponic_ph | rest.chemistry.v1 | rest |
  | air_quality_voc | rest.chemistry.v1 | rest |
  | air_quality_pm25 | rest.particulate.v1 | rest |
  | water_tank_level | rest.level.v1 | rest |
  | solar_array | topic.power.v1 | telemetry |
  | power_bus | topic.power.v1 | telemetry |
  | power_consumption | topic.power.v1 | telemetry |
  | radiation | topic.environment.v1 | telemetry |
  | life_support | topic.environment.v1 | telemetry |
  | thermal_loop / primary | topic.thermal_loop.v1 | telemetry |
  | airlock-1 | topic.airlock.v1 | telemetry |

- UNIFIED EVENT SCHEMA:

  **UnifiedEvent** : | **event_id** (UUID) | source_type | source_id | schema_family | timestamp | metrics[] | status | state_label | raw |

  **Metric** : | **name** | value | unit |

- KAFKA TOPICS CONSUMED:

  | Topic | Description |
  | ----- | ----------- |
  | raw-sensor-events | Raw simulator payloads from ingestion-service |

- KAFKA TOPICS PRODUCED:

  | Topic | Description | User Stories |
  | ----- | ----------- | ------------ |
  | normalized-events | UnifiedEvent objects — consumed by realtime-service and actuator-rules-service | 1, 2, 3, 5, 6, 8, 9 |

---

## CONTAINER_NAME: actuator-rules-service

### DESCRIPTION

The actuator-rules-service evaluates automation rules against every incoming normalized event and publishes actuator commands when rule conditions are satisfied.

On every Kafka event received, the service loads all enabled rules from the database and evaluates each rule's condition against the event. Rules are loaded on-demand on every event — not cached in memory — so that newly enabled or created rules take effect immediately on the next event without any restart. Rule evaluation is entirely event-driven with no timer or scheduled polling.

### USER STORIES

11, 12, 13, 18, 20

### PORTS

8003:8003

### PERSISTENCE EVALUATION

The actuator-rules-service requires read-only access to the PostgreSQL `rules` table to load enabled rules on every event. It does not write to the database.

### EXTERNAL SERVICES CONNECTIONS

- PostgreSQL database (read-only, rules table)

### MICROSERVICES

#### MICROSERVICE: actuator-rules-service

- TYPE: backend
- PORTS: 8003
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - asyncpg: async PostgreSQL client for direct database queries (not SQLAlchemy)
    - aiokafka: async Kafka consumer (normalized-events) and producer (actuator-commands)
    - asyncio: manages the background rule evaluation loop

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, Kafka and database initialization, background task
    - `services/event_processor.py`: Kafka consumer loop, calls rule engine on every event
    - `services/rule_engine.py`: parses rule DSL with regex, evaluates conditions, returns actuator commands
    - `services/rules_repository.py`: loads enabled rules from PostgreSQL on every call (no in-memory cache)
    - `models/unified_event.py`: shared UnifiedEvent schema definition
    - `models/actuator_command.py`: ActuatorCommand model

- RULE DSL FORMAT:

  ```
  IF {sensor} {operator} {threshold} {unit} THEN set {actuator} to {ON|OFF}
  ```

  Supported operators: `<`, `<=`, `=`, `>=`, `>`

  Rule evaluation uses `metrics[0].value` compared against the threshold. Matching is performed on `source_id`.

- KAFKA TOPICS CONSUMED:

  | Topic | Description |
  | ----- | ----------- |
  | normalized-events | UnifiedEvent objects from processing-service |

- KAFKA TOPICS PRODUCED:

  | Topic | Description | User Stories |
  | ----- | ----------- | ------------ |
  | actuator-commands | { actuator_id, command: ON\|OFF } — consumed by actuator-management-service | 11, 12, 13, 20 |

---

## CONTAINER_NAME: rule-management-service

### DESCRIPTION

The rule-management-service provides a REST CRUD API for managing automation rules. It is responsible exclusively for persisting rules — it does not evaluate them.

Operators can create, update, enable, disable, and delete rules through this service. All rules are stored in PostgreSQL.

### USER STORIES

11, 12, 13, 14, 15, 16, 17

### PORTS

8004:8004

### PERSISTENCE EVALUATION

The rule-management-service requires persistent storage to maintain rule definitions. Rules are stored in a PostgreSQL table with fields: id, name, condition, action, enabled.

### EXTERNAL SERVICES CONNECTIONS

The rule-management-service does not connect to external services.

### MICROSERVICES

#### MICROSERVICE: rule-management-service

- TYPE: backend
- PORTS: 8004
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - SQLAlchemy (async): ORM for rule CRUD operations
    - PostgreSQL: persistent storage for rule definitions
    - Pydantic: request/response schema validation

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, database initialization, router inclusion
    - `routes/rules.py`: REST API endpoints for rule CRUD
    - `models/database.py`: SQLAlchemy Rule model and database connection
    - `schemas/rule_schema.py`: Pydantic schemas for request/response validation
    - `services/rule_service.py`: business logic for rule operations

- ENDPOINTS:

  | HTTP METHOD | URL | Description | User Stories |
  | ----------- | --- | ----------- | ------------ |
  | GET | /api/rules | Returns all rules | 16, 17 |
  | POST | /api/rules | Creates a new rule | 11, 12, 13 |
  | GET | /api/rules/{id} | Returns a rule by ID | 17 |
  | PUT | /api/rules/{id} | Updates a rule (including enable/disable) | 14 |
  | DELETE | /api/rules/{id} | Deletes a rule | 15 |

- DB STRUCTURE:

  **Rule** : | **id** (UUID) | name | condition | action | enabled |

---

## CONTAINER_NAME: actuator-management-service

### DESCRIPTION

The actuator-management-service executes actuator commands by forwarding them to the IoT simulator. It handles both rule-triggered commands arriving from Kafka and manual commands sent directly from the frontend via HTTP.

After every command execution, the service updates the API Gateway cache and broadcasts the new actuator state to all connected frontend clients via WebSocket.

### USER STORIES

18, 19

### PORTS

8005:8005

### PERSISTENCE EVALUATION

The actuator-management-service does not require persistent storage.

### EXTERNAL SERVICES CONNECTIONS

- IoT Simulator (HTTP POST to execute actuator commands and GET to fetch states)
- api-gateway (HTTP POST to `/cache/actuators/update` after every command)

### MICROSERVICES

#### MICROSERVICE: actuator-management-service

- TYPE: backend
- PORTS: 8005
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - aiokafka: async Kafka consumer for the `actuator-commands` topic
    - httpx: async HTTP client for simulator calls and API Gateway cache updates
    - FastAPI WebSocket: broadcasts actuator state changes to connected frontend clients

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, Kafka consumer initialization, WebSocket endpoint, background task
    - `services/command_executor.py`: executes commands, updates cache, broadcasts WebSocket
    - `services/simulator_client.py`: HTTP client for simulator actuator API and state fetching
    - `services/websocket_manager.py`: manages connected WebSocket clients and broadcast
    - `kafka/consumer.py`: Kafka consumer for actuator-commands topic
    - `routes/actuators.py`: HTTP endpoints for manual actuator control

- ENDPOINTS:

  | HTTP METHOD | URL | Description | User Stories |
  | ----------- | --- | ----------- | ------------ |
  | GET | /api/actuators | Returns current state of all actuators from simulator | 19 |
  | POST | /api/actuators/{id} | Sends command { state: ON\|OFF } to actuator | 18, 19 |
  | POST | /api/actuators/{id}/on | Turns actuator ON (legacy endpoint) | 18 |
  | POST | /api/actuators/{id}/off | Turns actuator OFF (legacy endpoint) | 18 |
  | WS | /ws/actuators | WebSocket — broadcasts actuator state changes to frontend | 19 |

- KAFKA TOPICS CONSUMED:

  | Topic | Description |
  | ----- | ----------- |
  | actuator-commands | Actuator commands from actuator-rules-service |

- KNOWN ACTUATORS:

  | actuator_id | Label |
  | ----------- | ----- |
  | cooling_fan | Cooling Fan |
  | entrance_humidifier | Entrance Humidifier |
  | hall_ventilation | Hall Ventilation |
  | habitat_heater | Habitat Heater |

---

## CONTAINER_NAME: realtime-service

### DESCRIPTION

The realtime-service consumes normalized events from Kafka and broadcasts them in real time to all connected frontend clients via WebSocket. It also maintains an in-memory cache of the latest event per sensor and pushes updates to the API Gateway to support tab-switch cache restoration.

### USER STORIES

2, 6, 7, 8, 9

### PORTS

8006:8006

### PERSISTENCE EVALUATION

The realtime-service does not maintain persistent storage. Cache storage is handled by the api-gateway. The realtime-service only notifies the api-gateway of new events via HTTP POST.

### EXTERNAL SERVICES CONNECTIONS

- api-gateway (HTTP POST to `/cache/sensors/update` after every event)

### MICROSERVICES

#### MICROSERVICE: realtime-service

- TYPE: backend
- PORTS: 8006
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - aiokafka: async Kafka consumer for the `normalized-events` topic
    - FastAPI WebSocket: real-time event push to connected frontend clients
    - httpx: HTTP client for API Gateway cache update calls

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, WebSocket endpoint, Kafka listener startup
    - `services/kafka_listener.py`: Kafka consumer loop, posts event to API Gateway cache, broadcasts WebSocket
    - `services/websocket_manager.py`: manages connected WebSocket clients and broadcast

- WEBSOCKET ENDPOINT:

  | URL | Description | User Stories |
  | --- | ----------- | ------------ |
  | ws://localhost:8006/ws/events | Broadcasts full UnifiedEvent JSON for every normalized event | 2, 6, 7, 8, 9 |

- KAFKA TOPICS CONSUMED:

  | Topic | Description |
  | ----- | ----------- |
  | normalized-events | UnifiedEvent objects from processing-service |

---

## CONTAINER_NAME: api-gateway

### DESCRIPTION

The api-gateway provides a unified REST interface for the frontend. It proxies requests to internal backend services and maintains an in-memory cache of the latest sensor and actuator states to support tab-switching without data loss.

### USER STORIES

1, 16, 19

### PORTS

8000:8000

### PERSISTENCE EVALUATION

The api-gateway is the owner of the sensor and actuator cache. It maintains two in-memory dictionaries (`latest_sensor_data` and `latest_actuator_data`) that store the latest UnifiedEvent per `source_id` and the latest state per `actuator_id`. These dictionaries are updated by realtime-service and actuator-management-service respectively via HTTP POST. The cache is lost on restart, which is an accepted limitation.

### EXTERNAL SERVICES CONNECTIONS

The api-gateway proxies requests to internal microservices. It does not connect to external services directly.

### MICROSERVICES

#### MICROSERVICE: api-gateway

- TYPE: middleware
- PORTS: 8000
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in Python and uses FastAPI as the web framework.
  Key libraries and technologies:
    - httpx: async HTTP client for proxying requests to backend services

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.py`: application setup, global cache dictionaries, router inclusion
    - `routes/api.py`: proxy routes to backend services
    - `routes/cache.py`: cache read and write endpoints
    - `routes/health.py`: health check endpoint

- ENDPOINTS:

  | HTTP METHOD | URL | Description | User Stories |
  | ----------- | --- | ----------- | ------------ |
  | GET | /api/sensors | Proxy to IoT Simulator sensor list | 1 |
  | GET | /api/actuators | Proxy to actuator-management-service | 19 |
  | POST | /api/actuators/{id} | Forward actuator command | 18, 19 |
  | GET | /api/rules | Proxy to rule-management-service | 16 |
  | POST | /api/rules | Forward rule creation | 11 |
  | PUT | /api/rules/{id} | Forward rule update | 14 |
  | DELETE | /api/rules/{id} | Forward rule deletion | 15 |
  | GET | /api/sensors/latest | Return cached sensor data (UnifiedEvent per source_id) | 1, 2 |
  | GET | /api/actuators/latest | Return cached actuator states | 19 |
  | POST | /cache/sensors/update | Update sensor cache — called by realtime-service | — |
  | POST | /cache/actuators/update | Update actuator cache — called by actuator-management-service | — |

---

## CONTAINER_NAME: frontend

### DESCRIPTION

The frontend provides the web interface for habitat operators. It allows users to monitor sensors, visualize telemetry, manage automation rules, and manually control actuators.

It connects to the api-gateway for REST calls and maintains two persistent WebSocket connections — one to realtime-service for sensor and telemetry events, and one to actuator-management-service for actuator state changes.

### USER STORIES

1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20

### PORTS

5173:5173

### PERSISTENCE EVALUATION

The frontend does not include a database. All state is held in React memory during the session.

### EXTERNAL SERVICES CONNECTIONS

The frontend does not connect to external services.

### MICROSERVICES

#### MICROSERVICE: frontend

- TYPE: frontend
- PORTS: 5173
- TECHNOLOGICAL SPECIFICATION:
  The microservice is developed in JavaScript and uses React as the UI framework.
  Key libraries and technologies:
    - Vite: build tool and development server
    - Recharts: time-series line charts for sensor and telemetry visualization
    - WebSocket (native browser API): real-time event reception from backend services

- SERVICE ARCHITECTURE:
  The service is structured as follows:
    - `main.jsx`: React application entry point
    - `services/api.js`: HTTP client helpers (apiGet, apiPost, apiPut, apiDelete)
    - `services/websocket.js`: useWebSocketClient hook — manages both WebSocket connections, in-memory sensor state, history, and manual override logic
    - `pages/Dashboard.jsx`: sensor monitoring page
    - `pages/Telemetry.jsx`: telemetry monitoring page
    - `pages/Actuators.jsx`: manual actuator control page
    - `pages/Rules.jsx`: automation rule management page

- PAGES:

  | Name | Description | Related Services | User Stories |
  | ---- | ----------- | ---------------- | ------------ |
  | Dashboard.jsx | 8 REST sensor cards with primary value, trend chart, and alert indicators | api-gateway, realtime-service | 1, 2, 3, 4, 5, 9, 10, 20 |
  | Telemetry.jsx | 7 telemetry cards with primary metric chart and vertical secondary metrics list | api-gateway, realtime-service | 2, 6, 7, 8, 9 |
  | Actuators.jsx | Manual ON/OFF control for 4 actuators with 5-second override logic and trigger log | api-gateway, actuator-management-service | 18, 19 |
  | Rules.jsx | Rule list with create form, enable/disable toggle, delete, and mutual exclusion enforcement | api-gateway | 11, 12, 13, 14, 15, 16, 17, 18 |

- KEY DESIGN DECISIONS:
  - `useWebSocketClient` manages both WebSocket connections with automatic reconnect (3-second delay on disconnect)
  - Sensor cache is restored on component mount and on tab visibility change via `/api/sensors/latest`
  - State merge precedence: `cached data → WebSocket events → manual commands`
  - Manual override uses a timestamp ref — WebSocket events older than the last manual command are ignored for 5 seconds to prevent race conditions
  - When a manual actuator command is sent, all rules targeting that actuator are automatically disabled
  - Enabling a rule automatically disables all other rules targeting the same actuator (mutual exclusion)

---

## CONTAINER_NAME: Infrastructure

### DESCRIPTION

Provides the underlying infrastructure required for the system to operate. Includes the message broker, coordination service, database, and IoT simulator.

### PORTS

- Kafka: 9092
- Zookeeper: 2181
- PostgreSQL: 5432
- IoT Simulator: 8080

### PERSISTENCE EVALUATION

PostgreSQL provides persistent storage for the `rules` table, shared between rule-management-service and actuator-rules-service.

### EXTERNAL SERVICES CONNECTIONS

The infrastructure components do not connect to external services.

### COMPONENTS

| Component | Image | Port | Role |
| --------- | ----- | ---- | ---- |
| Kafka | confluentinc/cp-kafka:7.6.0 | 9092 | Central message bus for all inter-service event streaming |
| Zookeeper | confluentinc/cp-zookeeper:7.6.0 | 2181 | Kafka cluster coordination |
| PostgreSQL | postgres:16 | 5432 | Persistent storage for automation rules |
| IoT Simulator | mars-iot-simulator:multiarch_v1 | 8080 | Simulated Mars habitat sensors and actuator endpoints |