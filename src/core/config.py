from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
from src.core.logger import sys_logger


class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    PROJECT_NAME: str = "Traffic Light Detection"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf_8", extra="ignore"
    )


try:
    settings = Settings()
    sys_logger.info("System Config: Environment variables loaded successfully.")
except Exception as e:
    sys_logger.critical(
        "Failed to load environment variables. Please check your .env file."
    )
    sys_logger.error(f"Details: {e}")
    sys.exit(1)
