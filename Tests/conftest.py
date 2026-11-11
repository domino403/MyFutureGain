from dotenv import load_dotenv
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


# Tests/conftest.py -> katalog główny repozytorium
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_API_DIR = ROOT_DIR / "Source_Code" / "data_api"
ALEMBIC_CONFIG = DATA_API_DIR / "alembic.ini"
load_dotenv()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = os.environ.get("TEST_DATABASE_URL")

    if not database_url:
        pytest.fail("TEST_DATABASE_URL environment variable is not set.")

    local_database_url = os.environ.get("DATABASE_URL")

    if local_database_url and database_url == local_database_url:
        pytest.fail("Tests must not run against the local application database.")

    return database_url


@pytest.fixture(scope="session")
def migrated_database(test_database_url: str) -> str:
    # Verify database connectivity before running migrations.
    test_engine = create_engine(test_database_url)

    try:
        with test_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.fail(
            f"Cannot connect to TEST_DATABASE_URL.\n"
            f"Check PostgreSQL credentials and database availability.\n"
            f"Details: {exc}"
        )
    finally:
        test_engine.dispose()

    env = os.environ.copy()
    env["DATABASE_URL"] = test_database_url

    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(DATA_API_DIR), existing_pythonpath]))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ALEMBIC_CONFIG),
            "upgrade",
            "head",
        ],
        cwd=DATA_API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.fail(f"Alembic migration failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")

    return test_database_url


@pytest.fixture(scope="session")
def engine(migrated_database: str):
    engine = create_engine(
        migrated_database,
        pool_pre_ping=True,
    )

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
