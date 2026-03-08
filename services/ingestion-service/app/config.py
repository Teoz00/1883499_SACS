from pydantic import BaseSettings, AnyHttpUrl
from typing import Optional


class IngestionServiceSettings(BaseSettings):
    service_name: str = "ingestion-service"
    host: str = "0.0.0.0"
    port: int = 8001

    simulator_base_url: Optional[AnyHttpUrl] = None

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_raw_events: str = "raw-sensor-events"

    class Config:
        env_file = ".env"


settings = IngestionServiceSettings()

