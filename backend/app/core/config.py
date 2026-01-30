
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Prahari-AI Backend"
    API_V1_STR: str = "/api/v1"
    
    # AWS / LocalStack Config
    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT: str = "http://localhost:4566"
    AWS_ACCESS_KEY: str = "test"
    AWS_SECRET_KEY: str = "test"
    
    # Thresholds
    GEOFENCE_ALERT_DISTANCE_M: float = 50.0  # meters
    INACTIVITY_THRESHOLD_SECONDS: int = 1800 # 30 mins
    AUTH_API_KEY: str # Read from env
    
    class Config:
        env_file = ".env"

settings = Settings()
