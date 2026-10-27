"""
Run this after setting up PostgreSQL and filling in .env, to confirm
Python can actually reach your database before we build anything on top of it.

Run with:  python scripts/test_db_connection.py
"""
import sys
import os

# Allow importing config/ when running this script directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL


def main():
    print("Attempting to connect to:", DATABASE_URL.split("@")[-1])
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print("✅ Connected successfully.")
            print("PostgreSQL version:", version)
    except Exception as e:
        print("❌ Connection failed.")
        print("Error:", e)
        print("\nCommon causes:")
        print("- PostgreSQL isn't running")
        print("- DB_NAME / DB_USER / DB_PASSWORD in .env don't match what you created")
        print("- The database 'trendlens' hasn't been created yet")


if __name__ == "__main__":
    main()
