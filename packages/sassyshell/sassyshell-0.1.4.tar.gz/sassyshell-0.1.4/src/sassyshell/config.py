from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "sassyshell"
ENV_FILE = CONFIG_DIR / ".env"

class Settings(BaseSettings):
    data_file: Path = CONFIG_DIR / "sassy_db.json"
    llm_model_name: str = "gemini-2.5-flash"
    llm_model_provider: str = "google_genai"
    llm_api_key: str = ""
    max_history_size: int = 10

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
