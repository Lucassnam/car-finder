from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://carfinder:carfinder@localhost:5432/carfinder"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    llm_text_model: str = "qwen2.5:14b"
    llm_vision_model: str = "llama3.2-vision:11b"
    llm_embed_model: str = "nomic-embed-text"

    # Scraping — Craigslist
    cl_regions: str = "sfbay,sacramento,santacruz,monterey,stockton"
    cl_min_delay_sec: float = 3.0
    cl_max_delay_sec: float = 8.0

    # eBay (optional)
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_env: str = "PRODUCTION"

    # Alerts (optional)
    alert_ntfy_topic: str = ""
    alert_discord_webhook: str = ""
    alert_min_score: int = 8

    @property
    def cl_region_list(self) -> List[str]:
        return [r.strip() for r in self.cl_regions.split(",") if r.strip()]


settings = Settings()
