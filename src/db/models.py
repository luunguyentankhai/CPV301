# src/db/models.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from src.core.logger import sys_logger

# Log debug de kiem tra luong import cua he thong tren Terminal
sys_logger.debug("Database Models: Loading TrainingJob schema definition.")


class TrainingJob(SQLModel, table=True):
    __tablename__ = "training_jobs"

    job_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_name: str = Field(default="traffic-redlight-detection", max_length=100)
    dataset_path: str  # Da thay the git_repo_url bang dataset_path
    execution_command: str
    status: str = Field(default="PENDING", max_length=20)
    worker_id: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
