from fastapi import FastAPI

from app.routes.payments import router as payments_router
from app.routes.webhook import router as webhooks_router


app = FastAPI(title="Payments API", version="0.1.0")

app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"status": "ready"}
