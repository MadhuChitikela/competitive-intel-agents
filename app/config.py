from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    github_token: str = ""
    db_path: str = "data/p2_traces.db"


settings = Settings()
