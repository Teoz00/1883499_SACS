from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    """
    Common configuration shared across services.
    """

    kafka_bootstrap_servers: str = "kafka:9092"
    database_url: str = "postgresql://postgres:postgres@postgres:5432/rules-db"

    class Config:
        env_file = ".env"


common_settings = CommonSettings()

