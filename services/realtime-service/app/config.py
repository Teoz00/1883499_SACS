from pydantic_settings import BaseSettings, SettingsConfigDict


class RealtimeServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    service_name: str = "realtime-service"
    host: str = "0.0.0.0"
    port: int = 8006

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_normalized_events: str = "normalized-events"
    kafka_topic_actuator_events: str = "actuator-events"


settings = RealtimeServiceSettings()

