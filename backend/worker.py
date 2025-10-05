from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()


celery_app = Celery(
    "worker",
    broker = os.getenv("CELERY_BROKER_URL"),
    backend = os.getenv("CELERY_RESULT_BACKEND")
)