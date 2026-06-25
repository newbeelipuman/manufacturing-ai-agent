import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_DB_PATH = ROOT_DIR / "test_m2.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["TEST_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from app.db.base import Base
from app.db.session import engine
from app.main import app
from scripts.seed_demo_data import seed_demo_data


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    seed_demo_data()
    with TestClient(app) as test_client:
        yield test_client
