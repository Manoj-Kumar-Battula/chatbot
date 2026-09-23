from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PNW Knowledge Chatbot"
    api_version: str = "0.1.0"
    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
