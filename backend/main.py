from fastapi import FastAPI, File, UploadFile
from transformers import GenerationConfig
import models
from worker import process_document, model
from database import engine, SessionLocal
from models import DocumentChunk, QueryRequest
import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure
import os
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv


load_dotenv()


models.Base.metadata.create_all(bind=engine)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY) #type: ignore
gemini_model = genai.GenerativeModel('gemini-pro') #type: ignore


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
        generation_config = genai.GenerationConfig( #type: ignore
            temperature=0.2,
            max_output_tokens=800,
            top_p=0.8,
            top_k=40
        )
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return {"answer": response.text, "source_chunks": context}
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if db is not None:
            db.close()

    

    