from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from transformers import GenerationConfig
import models
from worker import process_document, model
from database import engine, SessionLocal
from models import DocumentChunk, QueryRequest
from fastapi.responses import StreamingResponse

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





SYSTEM_PROMPT = """SYSTEM_PROMPT = <prompt>
    <role>
        You are a world-class AI research assistant. Your sole purpose is to provide precise, factual answers based ONLY on the text provided in the <context> section.
    </role>

    <context>
    ---
    {context}
    ---
    </context>

    <user_question>
    {query}
    </user_question>

    <instructions>
        <thinking_steps>
            1.  First, deeply analyze the <user_question> to understand the specific information being requested.
            2.  Next, carefully scan all the text excerpts provided in the <context>. Identify every piece of information that is directly relevant to answering the user's question.
            3.  Synthesize the relevant information you've found into a draft answer. For each piece of information, make a mental note of its source chunk (e.g., [Chunk 1]).
            4.  Critically review your draft. Does it directly and fully answer the <user_question>? Is every statement in your draft supported by the <context>? If the information is not sufficient to answer the question, you must conclude that the answer is not available.
        </thinking_steps>
        <final_answer_rules>
            1.  Construct your final answer based ONLY on the synthesis from your thinking steps.
            2.  If the answer is not found in the context, your entire response must be ONLY the sentence: "I could not find an answer in the provided documents."
            3.  When you present the final answer, format it using clear Markdown.
            4.  You MUST cite the source chunk(s) at the end of each relevant sentence, like this:.
            5.  Do not include any information not present in the <context>.
        </final_answer_rules>
    </instructions>

    <output_format>
        First, provide your step-by-step reasoning inside <thinking> tags. After your reasoning, provide the final, user-facing answer inside <answer> tags.
    </output_format>
</prompt>"""

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