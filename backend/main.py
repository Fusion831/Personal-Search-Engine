from fastapi import FastAPI,File, UploadFile
from worker import process_document


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
    
    