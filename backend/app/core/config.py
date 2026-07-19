from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    MY_PHONE_NUMBER: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./stampede.db"
    DEMO_MODE: bool = False
    SIMULATE_STAMPEDE: bool = False
    
    # AI Pipeline Configuration
    STAMPEDE_CONFIDENCE_THRESHOLD: float = 0.90
    MIN_CONSECUTIVE_STAMPEDE_CLIPS: int = 3
    VIDEO_CLIP_LENGTH: int = 16
    VIDEO_STRIDE: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
