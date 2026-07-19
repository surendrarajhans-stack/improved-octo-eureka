from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nursing Home Management System"
    database_url: str = "sqlite:///./nursing_home.db"
    db_host: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_port: int = 5432
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    auto_create_schema: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if all([self.db_host, self.db_name, self.db_user, self.db_password]):
            return (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return "sqlite:///./nursing_home.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
