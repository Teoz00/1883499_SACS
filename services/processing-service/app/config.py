from pydantic import BaseSettings


class ProcessingServiceSettings(BaseSettings):
    service_name: str = "processing-service"
    host: str = "0.0.0.0"
    port: int = 8002

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_raw_events: str = "raw-sensor-events"
    kafka_topic_normalized_events: str = "normalized-events"

    class Config:
        env_file = ".env"


settings = ProcessingServiceSettings()

