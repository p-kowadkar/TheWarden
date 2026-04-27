from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Cloud
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"

    # AI Models
    model_standard: str = "gemini-2.5-flash-preview-05-20"
    model_critical: str = "gemini-2.5-pro-preview-05-06"

    # Database
    database_url: str = "postgresql://warden:password@localhost:5432/warden_db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Behaviour
    max_response_tokens: int = 400
    response_timeout_seconds: int = 8


settings = Settings()

# NPCs that require the critical (pro) model due to narrative complexity
CRITICAL_NPC_IDS = {"NPC-011", "NPC-012", "NPC-013", "NPC-S03"}
