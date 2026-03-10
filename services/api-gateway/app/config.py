from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiGatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    service_name: str = "api-gateway"
    host: str = "0.0.0.0"
    port: int = 8000

    # Backend base URLs for reverse proxy (defaults match docker-compose service names)
    sensors_service_url: str = "http://iot-simulator:8080"
    actuators_service_url: str = "http://actuator-management-service:8005"
    rules_service_url: str = "http://rule-management-service:8004"
    realtime_service_url: str = "http://realtime-service:8006"

    # Timeout for forwarding requests to backends (seconds)
    proxy_timeout_seconds: float = 30.0


settings = ApiGatewaySettings()

