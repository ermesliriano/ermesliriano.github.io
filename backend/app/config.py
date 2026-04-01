from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./dev.db"

    JWT_SECRET: str = "6d93dda4da9ed79772d4b3dda0a072ac448ef4ad3ac7de1de09d15ec8841b26f"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 14

    GOOGLE_WEB_CLIENT_ID: str  = "423467785550-6qeuu5n702rvbpumf6tl8mqe5gs4obh6.apps.googleusercontent.com" # el "client_id" de OAuth 2.0 (Web application)
    CORS_ORIGINS: str = "https://ermesliriano.github.io"

settings = Settings()
