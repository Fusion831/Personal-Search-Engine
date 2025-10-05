from fastapi import FastAPI,File, UploadFile


app = FastAPI()

@app.get("/")
def read_root():
    return {"Message" : "Check"}