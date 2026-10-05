from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PNW Knowledge Chatbot"
    api_version: str = "0.1.0"
    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    database_url: str = Field(
        default="postgresql+psycopg://pnw:pnw_local_password@localhost:5432/pnw_chatbot",
        alias="DATABASE_URL",
    )
    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
