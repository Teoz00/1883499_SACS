from pydantic import BaseSettings


class RealtimeServiceSettings(BaseSettings):
    service_name: str = "realtime-service"
    host: str = "0.0.0.0"
    port: int = 8006

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_normalized_events: str = "normalized-events"

    class Config:
        env_file = ".env"


settings = RealtimeServiceSettings()

