import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Find the .env file in the backend directory
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "OncoAI")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure_default_key_change_me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 11520))

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "oncoai")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: str = os.getenv("SMTP_PORT", "587")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Check for a full database URL first (standard for deployments like Render/Heroku)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            db_url = db_url.strip() # Remove any accidental spaces or newlines
            # SQLAlchemy requires "postgresql://" not "postgres://"
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return db_url

        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{user}:{password}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
