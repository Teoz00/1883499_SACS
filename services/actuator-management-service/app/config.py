from typing import Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class ActuatorManagementServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    service_name: str = "actuator-management-service"
    host: str = "0.0.0.0"
    port: int = 8005

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_actuator_commands: str = "actuator-commands"
    kafka_topic_actuator_events: str = "actuator-events"

    # Base URL of the external simulator (e.g. http://iot-simulator:8080)
    simulator_base_url: Optional[AnyHttpUrl] = None


settings = ActuatorManagementServiceSettings()

