import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL" #, "sqlite:///church_attendance.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-jwt")
    # token expiry seconds (integers)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("ACCESS_EXPIRES", 3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("REFRESH_EXPIRES", 86400))
