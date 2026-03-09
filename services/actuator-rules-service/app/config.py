from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class ActuatorRulesServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    service_name: str = "actuator-rules-service"
    host: str = "0.0.0.0"
    port: int = 8003

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_normalized_events: str = "normalized-events"
    kafka_topic_actuator_commands: str = "actuator-commands"

    database_url: PostgresDsn | str = "postgresql://postgres:postgres@postgres:5432/rules-db"


settings = ActuatorRulesServiceSettings()

