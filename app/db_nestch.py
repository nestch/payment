from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

nestch_engine = create_engine(
    settings.sqlalchemy_database_url,
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
