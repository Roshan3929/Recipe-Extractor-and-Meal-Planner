from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    tavily_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"
    llm_temperature: float = 0.3
    max_output_tokens: int = 2048
    scrape_char_limit: int = 5000
    request_timeout: int = 10
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = str(ENV_PATH)

settings = Settings()