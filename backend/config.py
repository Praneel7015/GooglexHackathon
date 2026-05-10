from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Gemini / ADK (GOOGLE_API_KEY is the canonical name ADK reads)
    # Multiple keys comma-separated for rotation when rate-limited
    gemini_api_key: str = ""
    gemini_api_keys: str = ""  # comma-separated: key1,key2,key3
    google_api_key: str = ""

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Twitter (twikit cookies)
    twitter_username: str = ""
    twitter_auth_token: str = ""
    twitter_ct0: str = ""

    # Email (Resend HTTP API — works on Railway)
    resend_api_key: str = ""
    gmail_user: str = ""
    gmail_app_password: str = ""

    # App
    environment: str = "dev"
    admin_secret: str = "nammacity-admin-2026"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
