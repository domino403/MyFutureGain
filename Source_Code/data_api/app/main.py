import os

from fastapi import FastAPI
from sqlalchemy import create_engine, text

from app.api.routers.historical_prices import router as prices_router
from app.api.routers.instruments import router as instruments_router


app = FastAPI(
    title="Portfolio Tracker Data API",
    version="0.1.0",
)

app.include_router(instruments_router, prefix="/api/v1")
app.include_router(prices_router, prefix="/api/v1")

database_url = os.environ["DATABASE_URL"]

engine = create_engine(database_url)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar_one()

    return {
        "status": "ok",
        "database": "connected",
        "test_query": value,
    }
