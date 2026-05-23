from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://muelaads:muelaads@localhost/muelaads"
    secret_key: str = "changeme-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    anthropic_api_key: str = ""
    blotato_api_key: str = ""
    r2_bucket: str = ""
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
