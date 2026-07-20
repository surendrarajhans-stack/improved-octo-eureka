from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    DATABASE_URL: str = "sqlite:///./hospital.db"
    DEBUG: bool = True

    HOSPITAL_NAME: str = "City General Hospital"
    HOSPITAL_PHONE: str = "+1 555 100 2000"
    HOSPITAL_EMAIL: str = "info@citygeneralhospital.com"
    HOSPITAL_ADDRESS: str = "100 Health Avenue, Springfield"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CURRENCY_SYMBOL: str = "₹"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
