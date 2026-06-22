from sqlmodel import create_engine, SQLModel, Session
from src.core.config import settings

from src.db.models import TrainingJob
from src.core.logger import sys_logger

engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)


def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        sys_logger.info(
            "Database Initialization: Tables created or verified successfully."
        )
    except Exception as e:
        sys_logger.error(
            f"Database Error: Failed to initialize database tables. Details: {e}"
        )


def get_session():
    with Session(engine) as session:
        yield session
