from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import settings

# Engine setup
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in db_url:
        engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(
    db_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_db_schema_compatibility(db_engine):
    """
    Ensure database columns match latest SQLAlchemy models.
    Handles column additions/renames seamlessly on PostgreSQL (Azure) and SQLite.
    """
    import logging
    db_logger = logging.getLogger("referral_portal.database")
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(db_engine)
        table_names = inspector.get_table_names()

        if "referrals" in table_names:
            cols = {col["name"]: col for col in inspector.get_columns("referrals")}

            storage_mappings = [
                ("sharepoint_drive_id", "storage_drive_id", "VARCHAR(255)"),
                ("sharepoint_item_id", "storage_item_id", "VARCHAR(255)"),
                ("sharepoint_file_id", "storage_file_id", "VARCHAR(255)"),
                ("sharepoint_file_url", "storage_file_url", "VARCHAR(1000)"),
            ]

            with db_engine.begin() as conn:
                for old_col, new_col, ddl_type in storage_mappings:
                    if new_col not in cols:
                        if old_col in cols:
                            try:
                                conn.execute(text(f"ALTER TABLE referrals RENAME COLUMN {old_col} TO {new_col}"))
                                db_logger.info(f"Renamed referrals column {old_col} to {new_col}")
                            except Exception as re_err:
                                db_logger.debug(f"Rename fallback: {re_err}")
                                conn.execute(text(f"ALTER TABLE referrals ADD COLUMN IF NOT EXISTS {new_col} {ddl_type}"))
                        else:
                            conn.execute(text(f"ALTER TABLE referrals ADD COLUMN IF NOT EXISTS {new_col} {ddl_type}"))
                            db_logger.info(f"Added column referrals.{new_col}")

                # Guarantee other columns
                if "referred_by_name" not in cols:
                    conn.execute(text("ALTER TABLE referrals ADD COLUMN IF NOT EXISTS referred_by_name VARCHAR(255)"))
                if "referred_by_email" not in cols:
                    conn.execute(text("ALTER TABLE referrals ADD COLUMN IF NOT EXISTS referred_by_email VARCHAR(255)"))
                if "candidate_consent" not in cols:
                    conn.execute(text("ALTER TABLE referrals ADD COLUMN IF NOT EXISTS candidate_consent BOOLEAN DEFAULT TRUE"))

        if "users" in table_names:
            user_cols = {col["name"]: col for col in inspector.get_columns("users")}
            with db_engine.begin() as conn:
                if "password" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR(255) DEFAULT ''"))
    except Exception as exc:
        db_logger.warning(f"Database schema compatibility auto-check note: {exc}")


def get_db():
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

