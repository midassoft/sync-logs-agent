import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LOG_STORAGE = os.getenv("LOG_STORAGE", "file")  # "file" o "database"

settings = Settings()
