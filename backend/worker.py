from celery import Celery
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from io import BytesIO
import logging
from database import SessionLocal, engine, Base
from models import ChildChunk, ParentChunk
import re

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
def process_document(file_contents, document_id):
    db = None
    try:
        db = SessionLocal()
        logger.info("Database session started.")

        
        reader = PdfReader(BytesIO(file_contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        
        
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  
        text = re.sub(r'\n{3,}', '\n\n', text)  
        text = re.sub(r' +', ' ', text)  
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        parent_chunk_objects = []
        child_chunk_texts = [] 
        parent_child_map = {} 

        for paragraph in paragraphs:
            
            if len(paragraph) < 50:
                continue

            
            parent_chunk = ParentChunk(document_id=document_id, content=paragraph)
            parent_chunk_objects.append(parent_chunk)
            parent_child_map[id(parent_chunk)] = [] 

            
            child_texts_for_parent = chunkText(paragraph, chunkSize=500, chunkOverlap=100)
            child_chunk_texts.extend(child_texts_for_parent)
            parent_child_map[id(parent_chunk)].extend(child_texts_for_parent)

        
        if not child_chunk_texts:
             logger.info("No text found to process.")
             return {"status": "success", "num_chunks": 0}

        logger.info(f"Encoding {len(child_chunk_texts)} child chunks in batch...")
        all_embeddings = model.encode(child_chunk_texts).tolist()
        logger.info("Encoding complete.")

        
        embedding_index = 0
        for parent_obj in parent_chunk_objects:
            
            db.add(parent_obj)
            db.flush()

           
            child_texts = parent_child_map[id(parent_obj)]
            for child_text in child_texts:
                embedding = all_embeddings[embedding_index]
                child_chunk = ChildChunk(
                    parent_chunk_id=parent_obj.id,
                    content=child_text,
                    embedding=embedding
                )
                db.add(child_chunk)
                embedding_index += 1

        
        db.commit()
        logger.info("Successfully committed all parent and child chunks.")
        return {"status": "success", "num_chunks": len(child_chunk_texts)}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if db:
            db.rollback() # Roll back the transaction on error
        return {"status": "error", "message": str(e)}

    finally:
        # ALWAYS close the session
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




        