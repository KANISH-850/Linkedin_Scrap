"""Test Alembic migrations against a real disposable PostgreSQL database."""

import os
import subprocess
import psycopg
import pytest
from sqlalchemy import create_engine, inspect, text

PG_ADMIN_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
DISPOSABLE_DB_NAME = "test_referralpilot_disposable"
DISPOSABLE_URL = f"postgresql+psycopg://postgres:postgres@localhost:5432/{DISPOSABLE_DB_NAME}"

@pytest.fixture(scope="module")
def postgres_disposable_db():
    # Setup disposable DB
    with psycopg.connect(PG_ADMIN_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DISPOSABLE_DB_NAME}' AND pid <> pg_backend_pid()")
            cur.execute(f"DROP DATABASE IF EXISTS {DISPOSABLE_DB_NAME}")
            cur.execute(f"CREATE DATABASE {DISPOSABLE_DB_NAME}")
    yield DISPOSABLE_URL
    # Teardown
    with psycopg.connect(PG_ADMIN_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DISPOSABLE_DB_NAME}' AND pid <> pg_backend_pid()")
            cur.execute(f"DROP DATABASE IF EXISTS {DISPOSABLE_DB_NAME}")

def test_alembic_migration_on_postgres(postgres_disposable_db):
    env = os.environ.copy()
    env["DATABASE_URL"] = DISPOSABLE_URL
    env["PYTHONPATH"] = "."

    # 1. Run alembic upgrade head
    res = subprocess.run(
        [".\\.venv\\Scripts\\alembic.exe", "upgrade", "head"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Alembic upgrade failed: {res.stderr}\n{res.stdout}"

    # 2. Inspect tables and columns
    engine = create_engine(DISPOSABLE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        "user_accounts",
        "user_profiles",
        "skills",
        "projects",
        "discovery_sources",
        "opportunities",
        "opportunity_scores",
        "eligibility_assessments",
        "opportunity_evidences",
        "applications",
        "interactions",
        "follow_ups",
        "discovery_runs",
        "notifications",
        "user_settings",
    ]
    for tbl in required_tables:
        assert tbl in tables, f"Missing table: {tbl}"

    # Verify opportunities columns
    opp_cols = {c["name"]: c for c in inspector.get_columns("opportunities")}
    assert "opportunity_type" in opp_cols, "Missing column opportunity_type"
    assert "application_status" in opp_cols, "Missing column application_status"
    assert "verification_status" in opp_cols, "Missing column verification_status"
    assert "dedup_hash" in opp_cols, "Missing column dedup_hash"

    # Verify unique index/constraint on dedup_hash
    unique_constraints = inspector.get_unique_constraints("opportunities")
    indexes = inspector.get_indexes("opportunities")
    has_dedup_unique = any("dedup_hash" in u.get("column_names", []) for u in unique_constraints) or any(
        idx.get("unique") and "dedup_hash" in idx.get("column_names", []) for idx in indexes
    )
    assert has_dedup_unique, "Missing unique constraint on dedup_hash in opportunities"

    # 3. Test insertions with defaults and foreign keys
    from sqlalchemy.orm import Session
    from app.models.models import UserAccount, DiscoverySource, Opportunity

    with Session(engine) as session:
        user = UserAccount(email="test@example.com", hashed_password="hash", full_name="Test User", role="admin")
        session.add(user)

        src = DiscoverySource(name="Test Source", adapter_key="test_src", source_type="api", enabled=True)
        session.add(src)

        opp = Opportunity(
            title="AI Intern",
            organization="TestCorp",
            category="internships",
            source_url="https://test.com/1",
            canonical_url="https://test.com/1",
            dedup_hash="hash001",
            description="Test desc",
        )
        session.add(opp)
        session.commit()

        # Query and verify defaults
        saved_opp = session.query(Opportunity).filter(Opportunity.dedup_hash == "hash001").first()
        assert saved_opp is not None
        assert saved_opp.opportunity_type == "JOB"  # Default
        assert saved_opp.application_status == "UNVERIFIED"  # Audited safe default

    # Dispose connection pool before downgrade/drop
    engine.dispose()

    # 4. Test Alembic downgrade to verify rollback safety
    res_down = subprocess.run(
        [".\\.venv\\Scripts\\alembic.exe", "downgrade", "-1"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_down.returncode == 0, f"Alembic downgrade failed: {res_down.stderr}\n{res_down.stdout}"

    # Verify column default was rolled back to OPEN on ed7eabf5ed40
    engine2 = create_engine(DISPOSABLE_URL)
    inspector_down = inspect(engine2)
    opp_cols_down = {c["name"]: c for c in inspector_down.get_columns("opportunities")}
    assert "application_status" in opp_cols_down
    assert "'OPEN'" in (opp_cols_down["application_status"]["default"] or "")
    engine2.dispose()

    # Re-upgrade to head
    res_up = subprocess.run(
        [".\\.venv\\Scripts\\alembic.exe", "upgrade", "head"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_up.returncode == 0, f"Alembic re-upgrade failed: {res_up.stderr}\n{res_up.stdout}"
