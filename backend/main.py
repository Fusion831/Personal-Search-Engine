from fastapi import FastAPI,File, UploadFile
import models
from worker import process_document,model
from database import engine, SessionLocal
from models import DocumentChunk, QueryRequest

models.Base.metadata.create_all(bind=engine)


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
    try:
        queryVector = model.encode([request.query])[0] #returns a 2D array, but we only need the embedding vector
        db = SessionLocal()
        similar_chunks = db.query(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(queryVector)).limit(5).all()
    except Exception as e:
        return {"error": str(e)}

    return {"received_question": request.query}
    
    