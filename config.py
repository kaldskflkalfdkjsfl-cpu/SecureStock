import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'securestock.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    # Server-enforced absolute session lifetime (8 hours). The cookie may outlive
    # this, but the server rejects the session once this limit is exceeded.
    PERMANENT_SESSION_LIFETIME = 28800
    # Idle timeout (30 minutes) and absolute timeout (8 hours) enforced server
    # side on every request, independent of the signed cookie lifetime.
    SESSION_IDLE_TIMEOUT = 1800
    SESSION_ABSOLUTE_TIMEOUT = 28800

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")

    WTF_CSRF_TIME_LIMIT = 3600

    PAGINATION_PER_PAGE = 20

    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"
