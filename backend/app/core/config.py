from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SAKHI"
    API_V1_STR: str = "/api/v1"
    
    # Routing Provider Configuration
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    OSRM_PROFILE: str = "foot"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
