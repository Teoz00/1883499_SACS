from pydantic import BaseSettings, AnyHttpUrl
from typing import Optional


class ApiGatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    host: str = "0.0.0.0"
    port: int = 8000

    # Downstream service base URLs (placeholders)
    ingestion_service_url: Optional[AnyHttpUrl] = None
    processing_service_url: Optional[AnyHttpUrl] = None
    rule_management_service_url: Optional[AnyHttpUrl] = None
    actuator_management_service_url: Optional[AnyHttpUrl] = None
    realtime_service_url: Optional[AnyHttpUrl] = None

    class Config:
        env_file = ".env"


settings = ApiGatewaySettings()

