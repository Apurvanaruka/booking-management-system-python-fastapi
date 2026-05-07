from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare Appointment System"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/healthcare")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:5173"]

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    # OTP settings
    OTP_EXPIRY_MINUTES: int = 5
    OTP_DEV_MODE: bool = True  # Set to False in production

    class Config:
        case_sensitive = True


settings = Settings()
