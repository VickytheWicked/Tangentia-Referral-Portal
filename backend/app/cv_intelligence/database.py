import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("cv_intelligence")

# Ensure directory exists for the isolated SQLite database
db_path = settings.CV_INTELLIGENCE_DB_PATH
os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

# Dedicated engine for CV Intelligence SQLite DB
cv_engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
)

# Dedicated sessionmaker and Base, completely separated from core portal DB
CVSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cv_engine)
CVBase = declarative_base()


def init_cv_db():
    """Initialize CV Intelligence tables and restore from Azure Blob if configured."""
    try:
        from app.cv_intelligence.blob_sync import (
            download_cv_db_from_blob,
            upload_cv_db_to_blob,
            is_cv_blob_sync_enabled,
        )

        if is_cv_blob_sync_enabled():
            restored = download_cv_db_from_blob(db_path)
            logger.info(f"CV Intelligence Azure Blob restore on startup: {restored}")

        CVBase.metadata.create_all(bind=cv_engine)
        logger.info(f"CV Intelligence SQLite database initialized at {db_path}")

        # Ensure fit_summary column exists in existing SQLite database
        try:
            import sqlite3
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(job_matches)")
                cols = [r[1] for r in cur.fetchall()]
                if cols and "fit_summary" not in cols:
                    cur.execute("ALTER TABLE job_matches ADD COLUMN fit_summary TEXT")
                    conn.commit()
                    logger.info("Migrated job_matches table: successfully added fit_summary column.")
                if cols and "requirement_analysis" not in cols:
                    cur.execute("ALTER TABLE job_matches ADD COLUMN requirement_analysis TEXT")
                    conn.commit()
                    logger.info("Migrated job_matches table: successfully added requirement_analysis column.")
                conn.close()
        except Exception as mig_err:
            logger.warning(f"Failed to check/migrate job_matches columns: {mig_err}")

        if is_cv_blob_sync_enabled():
            upload_cv_db_to_blob(db_path)
    except Exception as e:
        logger.error(f"Failed to initialize CV Intelligence database: {e}", exc_info=True)


def get_cv_db():
    """FastAPI dependency for isolated CV Intelligence database session."""
    db = CVSessionLocal()
    try:
        yield db
    finally:
        db.close()
