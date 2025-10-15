import logging

import alembic.command
import alembic.config
from sqlmodel import create_engine

from .const import DATABASE_URL, EVAL_ASSIST_DIR, STORAGE_ENABLED
from .model import AppUser, LogRecord, StoredTestCase  # noqa: F401

logger = logging.getLogger(__name__)

engine = None
if STORAGE_ENABLED:
    engine = create_engine(DATABASE_URL)

    alembic_cfg = alembic.config.Config(
        EVAL_ASSIST_DIR / "alembic.ini", config_args={"sqlalchemy.url": DATABASE_URL}
    )
    try:
        alembic.command.upgrade(alembic_cfg, "head")
    except Exception as e:
        logger.exception(f"Error running migrations: {e}")
