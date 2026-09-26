from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    github_token: str = ""
    db_path: str = "data/p2_traces.db"

    class Config:
        env_file = ".env"


settings = Settings()
