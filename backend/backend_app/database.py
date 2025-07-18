import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from .models import Base

# Environment-aware DB config
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cleanup_db")
POSTGRES_HOST = "db" if IS_DOCKER else "localhost"
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 🔍 Print database connection string (without password for security)
print("🔍 Using DB URL:", f"postgresql://{POSTGRES_USER}:****@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# Retry logic
max_retries = 10
for i in range(max_retries):
    try:
        engine = create_engine(DATABASE_URL, future=True)
        with engine.connect():
            pass  # Actually test the connection
        SessionLocal = sessionmaker(bind=engine)
        print("✅ Database connected.")
        break
    except OperationalError:
        print(f"⏳ Database not ready, retrying in 3s... ({i+1}/{max_retries})")
        time.sleep(3)
else:
    raise Exception("❌ Database connection failed after multiple retries.")

def init_db():
    Base.metadata.create_all(bind=engine)
