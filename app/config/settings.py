from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    google_credentials_path: str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # Add more settings as needed

settings = Settings()
