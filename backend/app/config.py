from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./dev.db"

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 14

    GOOGLE_WEB_CLIENT_ID: str  # el "client_id" de OAuth 2.0 (Web application)
    CORS_ORIGINS: str = "https://ermesliriano.github.io"

settings = Settings()