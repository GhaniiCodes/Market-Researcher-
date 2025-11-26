import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Load environment variables lazily
        self._groq_api_key = None
        self._news_api_key = None
        self._rapidapi_key = None
        self._validated = False
    
    @property
    def GROQ_API_KEY(self):
        if self._groq_api_key is None:
            self._groq_api_key = os.getenv("GROQ_API_KEY")
        return self._groq_api_key
    
    @property
    def NEWS_API_KEY(self):
        if self._news_api_key is None:
            self._news_api_key = os.getenv("NEWS_API_KEY")
        return self._news_api_key
    
    @property
    def RAPIDAPI_KEY(self):
        if self._rapidapi_key is None:
            self._rapidapi_key = os.getenv("RAPIDAPI_KEY")
        return self._rapidapi_key
    
    def validate(self):
        """Validate that all required API keys are present"""
        if self._validated:
            return
        
        missing = []
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not self.NEWS_API_KEY:
            missing.append("NEWS_API_KEY")
        if not self.RAPIDAPI_KEY:
            missing.append("RAPIDAPI_KEY")
        
        if missing:
            raise EnvironmentError(f"Missing API keys in environment: {', '.join(missing)}")
        
        self._validated = True

# Create settings instance (no validation at import time)
settings = Settings()