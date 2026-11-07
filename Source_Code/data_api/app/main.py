import os

from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

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
