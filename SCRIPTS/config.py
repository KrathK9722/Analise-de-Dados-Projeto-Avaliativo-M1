import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "viagens_db")
DB_USER = os.getenv("DB_USER", "projeto_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    "1b9Yc_s9gm6TAERY3BjOw2bixu70X3tZL"
)
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID", "")
DATA_DIR = BASE_DIR / "data"
