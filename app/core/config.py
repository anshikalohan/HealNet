import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # App Settings
    PROJECT_NAME: str = "HealNet"
    API_V1_STR: str = "/api/v1"
    
    # ML Models Path
    MODELS_PATH: str = os.getenv("MODELS_PATH", "app/models")
    
    # APIs
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "healnet.db")
    
    # File uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/healnet_uploads")

settings = Settings()
