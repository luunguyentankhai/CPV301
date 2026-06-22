# src/core/celery.py
from celery import Celery
from src.core.config import settings
from src.core.logger import sys_logger

sys_logger.debug("Celery Config: Initializing Celery app instance.")

# Khởi tạo một đối tượng Celery app với Broker là RabbitMQ CloudAMQP
celery_app = Celery("central_controller", broker=settings.RABBITMQ_URL)

# Tối ưu hóa cấu hình cho mạng Cloud (Sử dụng định dạng JSON cho nhẹ và an toàn)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
