"""
Central place that loads environment variables so every other module
(data_collection, backend, analysis, etc.) imports from here instead of
each calling os.getenv() separately. This means if a variable name ever
changes, you fix it in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file in the project root

# --- Database ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "trendlens")
DB_USER = os.getenv("DB_USER", "trendlens_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- API keys (used from Phase 3 onward) ---
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "")
