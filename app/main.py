import time

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import engine
from app.models.base import Base
import app.models.payment
import app.models.user
from app.models.payment import Payment
from app.routes.auth import router as auth_router
from app.routes.payments import router as payments_router
from app.routes.simulate import router as simulate_router
from app.routes.webhook import router as webhooks_router


app = FastAPI(title="Payments API", version="0.1.0")


@app.on_event("startup")
def _startup():
    if settings.app_env == "dev":
        for _ in range(30):
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                break
            except OperationalError:
                time.sleep(1)
        Base.metadata.drop_all(bind=engine, tables=[Payment.__table__])
        Base.metadata.create_all(bind=engine, tables=[Payment.__table__])

app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(simulate_router)
app.include_router(webhooks_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"status": "ready"}
