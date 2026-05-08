from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Gemini
    gemini_api_key: str = ""

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Twitter
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""

    # Gmail
    gmail_user: str = ""
    gmail_app_password: str = ""

    # App
    environment: str = "dev"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
