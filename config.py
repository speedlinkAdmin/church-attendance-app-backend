import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    
    # Database URL with PostgreSQL format fix for Render
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 🎯 DATABASE CONNECTION POOLING CONFIGURATION
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,           # Recycle connections after 5 minutes
        'pool_pre_ping': True,         # Check connection health before use
        'pool_size': 5,               # Number of persistent connections
        'max_overflow': 9,            # Additional temporary connections allowed
        'pool_timeout': 30,            # Wait 30 seconds for a connection
    }

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-jwt")
    # token expiry seconds (integers)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("ACCESS_EXPIRES", 3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("REFRESH_EXPIRES", 86400))
    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
    SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")

    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '808921198974802')
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')










# import os
# from dotenv import load_dotenv
# load_dotenv()

# class Config:
#     SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         "DATABASE_URL" #, "sqlite:///church_attendance.db"
#     )
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

#     JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-jwt")
#     # token expiry seconds (integers)
#     JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("ACCESS_EXPIRES", 3600))
#     JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("REFRESH_EXPIRES", 86400))
#     SMTP_SERVER = os.environ.get("SMTP_SERVER")
#     SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
#     EMAIL_USER = os.environ.get("EMAIL_USER")
#     EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
#     SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")

