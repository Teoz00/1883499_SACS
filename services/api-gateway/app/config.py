from pydantic import BaseSettings


class ApiGatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    host: str = "0.0.0.0"
    port: int = 8000

    # Backend base URLs for reverse proxy (defaults match docker-compose service names)
    sensors_service_url: str = "http://iot-simulator:8080"
    actuators_service_url: str = "http://actuator-management-service:8005"
    rules_service_url: str = "http://rule-management-service:8004"

    # Timeout for forwarding requests to backends (seconds)
    proxy_timeout_seconds: float = 30.0

    class Config:
        env_file = ".env"


settings = ApiGatewaySettings()

