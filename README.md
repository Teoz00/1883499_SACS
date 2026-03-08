## IoT Event Processing Platform (Monorepo)

This repository contains a microservices-based IoT event processing
platform. The current state is **boilerplate only**: there is no
business logic, only structure and minimal scaffolding for services,
frontend, and infrastructure.

### High-Level Architecture

- **Event pipeline**:
  - Simulator → `ingestion-service` → Kafka (`raw-sensor-events`)
  - Kafka (`raw-sensor-events`) → `processing-service` → Kafka (`normalized-events`)
  - Kafka (`normalized-events`) → `actuator-rules-service` → Kafka (`actuator-commands`)
  - Kafka (`actuator-commands`) → `actuator-management-service` → Simulator / actuators
- **Realtime updates**:
  - Kafka (`normalized-events`) → `realtime-service` (WebSocket) → Frontend
- **User actions**:
  - Frontend → `api-gateway` → backend microservices

### Repository Layout

- `services/`
  - `api-gateway/`
  - `ingestion-service/`
  - `processing-service/`
  - `actuator-rules-service/`
  - `rule-management-service/`
  - `actuator-management-service/`
  - `realtime-service/`
- `frontend/` – React + Vite SPA with Dashboard, Rules, and Actuators pages, packaged as a Dockerized microservice.
- `shared/`
  - `event-schema/` – shared `UnifiedEvent` Pydantic model.
  - `config/` – common configuration placeholders.
- `infrastructure/`
  - `kafka/` – Kafka topic documentation.
  - `postgres/` – initial schema for `rules` table.
- `docker-compose.yml` – orchestrates Kafka, Zookeeper, Postgres, all services, the simulator container, and the frontend.

### Microservice Structure

Each backend service follows the same structure:

- `app/main.py` – FastAPI app initialization, health endpoint wiring.
- `app/routes/` – routers including a `/health` endpoint.
- `app/services/` – placeholders for core service logic.
- `app/models/` – placeholders for service-specific models.
- `app/kafka/` – aiokafka client placeholders (where applicable).
- `app/config.py` – Pydantic settings with environment variable support.
- `requirements.txt` – Python dependencies.
- `Dockerfile` – container definition for the service.

### Shared Event Schema

The unified event schema is defined in `shared/event-schema/unified_event.py`
as a Pydantic model `UnifiedEvent` with:

- `event_id`
- `sensor_id`
- `type`
- `value`
- `timestamp`

### Datastore

- **PostgreSQL**:
  - Database: `rules-db`
  - Table placeholder: `rules` (`id`, `name`, `condition`, `action`, `enabled`)
  - Initialization script: `infrastructure/postgres/init.sql`

### Kafka Topics

The platform uses the following Kafka topics (auto-created by Kafka):

- `raw-sensor-events`
- `normalized-events`
- `actuator-commands`

### Running with Docker Compose

From the repository root:

```bash
docker compose up
```

This will start:

- Zookeeper
- Kafka
- PostgreSQL
- All backend microservices
- The external simulator container (referenced by image)
- The React + Vite frontend

Environment variables:

- `KAFKA_BOOTSTRAP_SERVERS` – configured as `kafka:9092` for services.
- `DATABASE_URL` – configured as `postgresql://postgres:postgres@postgres:5432/rules-db` for services that use Postgres.

### Next Steps

- Implement actual business logic inside each service.
- Add authentication, observability, and proper error handling.
- Wire real simulator and actuator integrations.
