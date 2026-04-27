from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Cloud
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"

    # AI Models
    model_standard: str = "gemini-3-flash-preview"
    model_critical: str = "gemini-3.1-pro-preview"

    # Fallback models (used on 503/429 after retries are exhausted)
    model_standard_fallback: str = "gemini-2.5-flash"
    model_critical_fallback: str = "gemini-2.5-pro"

    # Database
    database_url: str = "postgresql://warden:password@localhost:5432/warden_db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Behaviour
    max_response_tokens: int = 400
    response_timeout_seconds: int = 8


settings = Settings()

# NPCs that require the critical (pro) model due to narrative complexity.
# npc_009 = Clement (Council operative)
# npc_011 = Cornelia Ashford
# npc_012 = Marcus Wren
# npc_s03 = The Voice
CRITICAL_NPC_IDS = {"npc_011", "npc_012", "npc_009", "npc_s03"}
