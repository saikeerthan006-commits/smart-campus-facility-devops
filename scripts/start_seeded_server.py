"""Starts the FastAPI Smart Campus Facility Platform on port 8000 for live browser verification."""
import os
from pathlib import Path
import sys

import uvicorn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.main import app, set_store
import campus_model as m


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    db_path = root / "evidence" / "logs" / "live_dashboard.db"
    if db_path.exists():
        db_path.unlink()

    os.environ["APP_SECRET_KEY"] = "CampusSuperSecretSigningKey2026_CSA10_CO4!"
    os.environ["APP_VERSION"] = "v2.0.0-day4"
    store = m.Store(str(db_path))
    set_store(store)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
