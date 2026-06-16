import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

_DB_HOST: str = os.getenv("DB_HOST", "localhost")
_DB_PORT: str = os.getenv("DB_PORT", "3306")
_DB_NAME: str = "nestch_db"
_DB_USER: str = os.getenv("DB_USER", "root")
_DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

_NESTCH_DB_URL = f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"

nestch_engine = create_engine(
    _NESTCH_DB_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

NestchSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=nestch_engine)


def get_nestch_db_session():
    db = NestchSessionLocal()
    try:
        yield db
    finally:
        db.close()
