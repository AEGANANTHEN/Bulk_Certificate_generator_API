import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.config import settings

@pytest.fixture(scope="session")
def temp_storage():
    """Create a temporary storage directory for tests and cleanup after."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_cert_storage_"))
    original_storage = settings.STORAGE_DIR
    original_certs = settings.CERTIFICATES_DIR
    original_db_url = settings.DATABASE_URL
    
    test_db_path = temp_dir / "test.db"
    settings.STORAGE_DIR = temp_dir
    settings.CERTIFICATES_DIR = temp_dir / "certificates"
    settings.DATABASE_URL = f"sqlite:///{test_db_path}"
    settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    (temp_dir / "archives").mkdir(parents=True, exist_ok=True)

    # Re-bind app database engine to test db
    import app.database as app_db
    app_db.engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    app_db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_db.engine)
    app_db.Base.metadata.create_all(bind=app_db.engine)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    settings.STORAGE_DIR = original_storage
    settings.CERTIFICATES_DIR = original_certs
    settings.DATABASE_URL = original_db_url


@pytest.fixture(scope="function")
def test_db(temp_storage):
    """Provides a fresh database session and cleans tables between tests."""
    import app.database as app_db
    db = app_db.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables between test runs
        for table in reversed(app_db.Base.metadata.sorted_tables):
            app_db.engine.execute(table.delete()) if hasattr(app_db.engine, "execute") else None
            with app_db.engine.connect() as conn:
                conn.execute(table.delete())
                conn.commit()


@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c
