from pydantic import BaseSettings


class ActuatorManagementServiceSettings(BaseSettings):
    service_name: str = "actuator-management-service"
    host: str = "0.0.0.0"
    port: int = 8005

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_actuator_commands: str = "actuator-commands"

    class Config:
        env_file = ".env"


settings = ActuatorManagementServiceSettings()

