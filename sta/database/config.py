from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = "a-very-secure-default-secret-key-for-development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./sta_dev.db"


settings = Settings()
