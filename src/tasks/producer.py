# src/tasks/producer.py
from sqlmodel import Session
from src.core.logger import sys_logger
from src.db.connection import engine
from src.db.models import TrainingJob
from src.core.celery import celery_app


# Da thay doi tham so thanh dataset_path
def dispatch_training_job(
    project_name: str, dataset_path: str, execution_command: str
) -> str:
    """
    Ham nhan tham so, ghi mot ban ghi PENDING vao Database,
    sau do day tac vu (task) len RabbitMQ cho Worker xu ly.
    """
    sys_logger.info(
        f"Preparing to dispatch new training job for project: '{project_name}'"
    )

    with Session(engine) as session:
        new_job = TrainingJob(
            project_name=project_name,
            dataset_path=dataset_path,  # Truyen duong dan thu muc chuan xac
            execution_command=execution_command,
        )
        session.add(new_job)
        session.commit()
        session.refresh(new_job)

        job_id_str = str(new_job.job_id)
        sys_logger.info(f"Database: Job {job_id_str} created with status PENDING.")

    try:
        celery_app.send_task(
            "worker.run_yolo_training",
            kwargs={
                "job_id": job_id_str,
                "dataset_path": dataset_path,  # Gui kem duong dan len CloudAMQP
                "execution_command": execution_command,
            },
        )
        sys_logger.info(f"RabbitMQ: Task {job_id_str} successfully published to queue.")
    except Exception as e:
        sys_logger.error(f"RabbitMQ: Failed to publish task {job_id_str}. Details: {e}")
        with Session(engine) as session:
            new_job.status = "FAILED"
            session.add(new_job)
            session.commit()
            sys_logger.info(f"Database: Job {job_id_str} status reverted to FAILED.")

    return job_id_str
