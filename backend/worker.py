from celery import Celery
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()



celery_app = Celery(
    "worker",
    broker = os.getenv("CELERY_BROKER_URL"),
    backend = os.getenv("CELERY_RESULT_BACKEND")
)
model = SentenceTransformer("all-MiniLM-L6-v2")






@celery_app.task
def process_document(file_contents):
    try:
        reader = PdfReader(BytesIO(file_contents))
        text =""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        chunks = chunkText(text, chunkSize=1000, chunkOverlap=200)
        embeddings = model.encode(chunks)
        logger.info(f"Processed {len(chunks)} chunks.")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1}: {chunk[:50]}...")  
            logger.info(f"Embedding {i+1}: {embeddings.shape}")
        return {"status": "success", "num_chunks": len(chunks)}

        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return {"status": "error", "message": str(e)}

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




        