import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "anomaly_detector_ped2.keras")
    RECONSTRUCTION_THRESHOLD: float = 0.02
    IMAGE_SIZE: tuple = (96, 96)
    FRAME_COUNT: int = 10
    DEVICE: str = "cpu"
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_DESTINATION_NUMBER: str = os.getenv("DESTINATION_PHONE_NUMBER") or os.getenv("MY_PHONE_NUMBER", "")

settings = Settings()
