import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Hiring Assistant"
    API_V1_STR: str = "/api/v1"
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"  # confirmed available on this API key

    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        if not self.GEMINI_API_KEY:
            print("⚠️  WARNING: GEMINI_API_KEY not set. Set it in .env or as an environment variable.")

settings = Settings()
