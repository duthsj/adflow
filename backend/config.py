from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql://muelaads:muelaads@localhost/muelaads"
    secret_key: str = "changeme-in-production"
    access_token_expire_minutes: int = 1440
    anthropic_api_key: str = ""
    blotato_api_key: str = ""
    r2_bucket: str = ""
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v == "changeme-in-production":
            import warnings
            warnings.warn("SECRET_KEY is using the default placeholder. Set a real value in .env before production.")
        return v

settings = Settings()
