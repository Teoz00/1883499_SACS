from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class IngestionServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    service_name: str = "ingestion-service"
    host: str = "0.0.0.0"
    port: int = 8001

    simulator_base_url: Optional[AnyHttpUrl] = None

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_raw_events: str = "raw-sensor-events"


settings = IngestionServiceSettings()

