import os

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database.connection import get_db

app = FastAPI()

database_url = os.environ["DATABASE_URL"]

engine = create_engine(database_url)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/example")
def example(db: Session = Depends(get_db)):
    # Database operations
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
