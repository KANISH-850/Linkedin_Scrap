"""CLI script to initialize or reset the admin account and seed candidate profile."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.seed import seed_database
from app.database.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        seed_database(db)
        print("Admin account, candidate profile, and default sources seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

