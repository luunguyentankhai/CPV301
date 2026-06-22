# src/main.py
import sys
from src.core.logger import sys_logger
from src.db.connection import init_db
from src.tasks.producer import dispatch_training_job


def main():
    """
    Ham khoi chay chinh cua Central Controller.
    """
    sys_logger.info("Starting Central Controller application...")

    # 1. Kich hoat qua trinh kiem tra va tao bang Database
    sys_logger.info("Attempting to initialize database connections and schemas...")
    init_db()

    # 2. Thu nghiem gui mot tac vu huan luyen
    sys_logger.info("Initiating a test dispatch for Celery Producer...")

    # Dinh nghia cac tham so
    test_project_name = "yolo-redlight-merged"
    # Truong duong dan den thu muc da gop tren Drive
    test_dataset_path = "/content/drive/MyDrive/CPV301/Data_Merge"
    test_command = (
        "yolo task=detect mode=train model=yolov8n.pt data=dataset.yaml epochs=50"
    )

    # Goi ham
    job_id = dispatch_training_job(
        project_name=test_project_name,
        dataset_path=test_dataset_path,
        execution_command=test_command,
    )

    sys_logger.info(
        f"Test dispatch completed successfully. Tracked with Job ID: {job_id}"
    )
    sys_logger.info("Application setup and test completed. Shutting down...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys_logger.info("Application interrupted by user. Shutting down...")
        sys.exit(0)
    except Exception as e:
        sys_logger.critical("Application encountered a fatal error and will shut down.")
        sys_logger.error(f"Error details: {e}")
        sys.exit(1)
