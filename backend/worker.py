from celery import Celery
import os
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()


celery_app = Celery(
    "worker",
    broker = os.getenv("CELERY_BROKER_URL"),
    backend = os.getenv("CELERY_RESULT_BACKEND")
)

def chunkText(text, chunkSize=1000, chunkOverlap=200):
        step = chunkSize - chunkOverlap
        chunks =[]
        start = 0
        while start < len(text):
            end = start + chunkSize
            chunk = text[start:end]
            chunks.append(chunk)
            start += step
        return chunks




@celery_app.task
def process_document(file_contents):
    try:
        reader = PdfReader(file_contents)
        text =""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        chunks = chunkText(text, chunkSize=1000, chunkOverlap=200)
        