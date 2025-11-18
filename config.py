import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

    @staticmethod
    def validate():
        missing = [key for key, val in [
            ("GROQ_API_KEY", Settings.GROQ_API_KEY),
            ("NEWS_API_KEY", Settings.NEWS_API_KEY),
            ("RAPIDAPI_KEY", Settings.RAPIDAPI_KEY),
        ] if not val]
        if missing:
            raise EnvironmentError(f"Missing API keys in .env: {', '.join(missing)}")

settings = Settings()
settings.validate()