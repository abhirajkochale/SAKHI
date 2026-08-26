from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SAKHI"
    API_V1_STR: str = "/api/v1"

    # Primary database connection URL
    DATABASE_URL: str = "sqlite:///./sakhi.db"

    # Supabase public project URL (used by frontend config, not backend DB)
    SUPABASE_URL: Optional[str] = None

    # Sarvam AI API key
    SARVAM_API_KEY: Optional[str] = None

    # Amenity discovery — Geoapify Places API (free tier, OSM-backed)
    # Register free at https://myprojects.geoapify.com/ — no credit card required
    GEOAPIFY_API_KEY: Optional[str] = None

    # Routing Provider Configuration
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    OSRM_PROFILE: str = "foot"

    # Phase 4 Route Ranking Prototype Coefficients
    # These are prototype decision parameters and are not empirically validated universal safety preferences.
    RANKING_SAFEST_ALPHA: float = 0.2
    RANKING_SAFEST_BETA: float = 0.7
    RANKING_SAFEST_GAMMA: float = 0.1

    RANKING_BALANCED_ALPHA: float = 0.4
    RANKING_BALANCED_BETA: float = 0.5
    RANKING_BALANCED_GAMMA: float = 0.1

    RANKING_FASTEST_ALPHA: float = 0.8
    RANKING_FASTEST_BETA: float = 0.1
    RANKING_FASTEST_GAMMA: float = 0.1

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # silently ignore unrecognised .env vars
    )


settings = Settings()
