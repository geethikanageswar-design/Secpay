import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "secpay_db")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    @property
    def database_url(self) -> str:
        # Encode password to safely handle special characters like '@'
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        # Connect to MySQL via PyMySQL
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
