from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings


class ActuatorManagementServiceSettings(BaseSettings):
    service_name: str = "actuator-management-service"
    host: str = "0.0.0.0"
    port: int = 8005

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_actuator_commands: str = "actuator-commands"

    # Base URL of the external simulator (e.g. http://simulator:8080)
    simulator_base_url: Optional[AnyHttpUrl] = None

    class Config:
        env_file = ".env"


settings = ActuatorManagementServiceSettings()

