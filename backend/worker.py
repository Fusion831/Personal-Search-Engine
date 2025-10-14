from celery import Celery
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from io import BytesIO
import logging
from database import SessionLocal, engine, Base
from models import DocumentChunk

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
@celery_app.task
def process_document(file_contents,document_id):
    db = None 
    try:
        
        db = SessionLocal()
        logger.info("Database session started.")

        
        reader = PdfReader(BytesIO(file_contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        chunks = chunkText(text, chunkSize=1000, chunkOverlap=200)
        embeddings = model.encode(chunks)
        logger.info(f"Created {len(chunks)} chunks and embeddings.")

        
        for chunk, embedding in zip(chunks, embeddings):
            new_chunk_obj = DocumentChunk(content=chunk, embedding=embedding, document_id=document_id)
            db.add(new_chunk_obj)

        
        db.commit()
        logger.info("Successfully committed all chunks to the database.")
        
        return {"status": "success", "num_chunks": len(chunks)}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if db:
            db.rollback()  
        return {"status": "error", "message": str(e)}

    finally:
        
        if db:
            db.close()
            logger.info("Database session closed.")

        
    

def chunkText(text, chunkSize=500, chunkOverlap=100):
        step = chunkSize - chunkOverlap
        chunks =[]
        start = 0
        while start < len(text):
            end = start + chunkSize
            chunk = text[start:end]
            chunks.append(chunk)
            start += step
        return chunks




        