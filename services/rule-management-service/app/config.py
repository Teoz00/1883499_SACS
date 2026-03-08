from pydantic import BaseSettings, PostgresDsn


class RuleManagementServiceSettings(BaseSettings):
    service_name: str = "rule-management-service"
    host: str = "0.0.0.0"
    port: int = 8004

    database_url: PostgresDsn | str = "postgresql://postgres:postgres@postgres:5432/rules-db"

    class Config:
        env_file = ".env"


settings = RuleManagementServiceSettings()

