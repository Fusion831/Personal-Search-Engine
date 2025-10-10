from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from transformers import GenerationConfig
import models
from worker import process_document, model
from database import engine, SessionLocal
from models import DocumentChunk, QueryRequest

from google import genai
from google.genai import types

import os

from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


models.Base.metadata.create_all(bind=engine)


client = genai.Client()





SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context.

Context from documents:
{context}

User Question: {query}

Instructions:
- Answer using ONLY the information from the context above
- Be concise and accurate
- Cite specific parts of the context when possible
- Do not make up information that isn't in the context

Answer:"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"Message" : "Check"}


@app.post("/Documents/upload")
async def upload_file(file: UploadFile = File(...)):
    """Read contents and send to celery"""
    contents = await file.read()
    task = process_document.delay(contents)
    return {"task_id": task.id, "status": "Processing started"}


@app.post("/query")
async def query_document(request: QueryRequest):
    """Query the Chunks with the vector embedding to find the most relevant chunks, and complete the RAG pipeline"""
    db = None
    try:
        
        queryVector = model.encode([request.query])[0] #returns a 2D array, but we only need the embedding vector
        db = SessionLocal()
        similar_chunks = db.query(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(queryVector)).limit(5).all()
        context = "\n\n".join([f"[Chunk {i+1}]: {chunk.content}" 
                               for i, chunk in enumerate(similar_chunks)])
        prompt = SYSTEM_PROMPT.format(context=context, query=request.query)
        response = client.models.generate_content(
            model = "gemini-2.5-flash",
            contents = prompt,
            config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
    ),
        )
        return {"answer": response.text, "source_chunks": context}
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if db is not None:
            db.close()