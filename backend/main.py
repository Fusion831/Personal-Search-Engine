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





SYSTEM_PROMPT = """<prompt>
<role>
You are a world-class AI research assistant. Your purpose is to provide precise, factual answers based ONLY on the text provided in the context section.
</role>

<context>
{context}
</context>

<user_question>
{query}
</user_question>

<chat_history>
{chat_history}
</chat_history>

<instructions>
<analysis_steps>
1. Carefully read and understand the user's question, and link it to the chat history if relevant.
2. Scan the context to identify all relevant information
3. Analyze the chat history to understand the flow of the conversation
4. Synthesize the information into a coherent answer
5. Ensure the answer is concise and directly addresses the user's question, and fits into the context of the conversation.
5. Verify that every statement is supported by the context
</analysis_steps>

<formatting_rules>
1. Use proper Markdown formatting for clarity and emphasis:
   - Use **bold** for important terms, key concepts, and definitions
   - Use *italics* for emphasis and subtle points
   - Use bullet points (- or *) or numbered lists (1. 2. 3.) when presenting multiple items
   - Use headers (## or ###) to organize complex information
   - Use > for blockquotes if citing specific passages
2. Structure your answer clearly with paragraphs and proper spacing
3. Make the response natural and readable - DO NOT include any XML tags in your output
4. DO NOT include chunk references like [Chunk 1], [Chunk 2] in your response
</formatting_rules>

<response_rules>
1. Answer using ONLY information from the context
2. If the answer is not in the context, respond ONLY with: "I could not find an answer in the provided documents."
3. Be DETAILED and COMPREHENSIVE in your explanations:
   - Provide full context and background information
   - Explain concepts thoroughly with examples when available
   - Include relevant details, characteristics, and nuances
   - Elaborate on key points rather than giving brief summaries
   - Connect related ideas and provide comprehensive understanding
4. Provide a natural, conversational, and descriptive response without any tags or metadata
5. Aim for depth and clarity - help the user truly understand the topic
</response_rules>
</instructions>

<output_format>
Provide your answer directly in clean Markdown format without any XML tags, thinking process, or metadata. Give a detailed, well-elaborated response that thoroughly addresses the question.
</output_format>
</prompt>"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"Message" : "Check"}


@app.get("/documents")
def getDocuments():
    """Fetch all documents"""
    db = SessionLocal()
    documents = db.query(models.Document).all()
    db.close()
    return documents


@app.post("/Documents/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    """Read contents and send to celery"""
    db = SessionLocal()
    task_results = []
    
    try:
        for file in files:
            contents = await file.read()
            Document_Object = models.Document(title=file.filename)
            db.add(Document_Object)
            db.commit()
            db.refresh(Document_Object)
            task = process_document.delay(contents, Document_Object.id)
            task_results.append({
                "filename": file.filename,
                "document_id": Document_Object.id,
                "task_id": task.id
            })
    finally:
        db.close()
    
    return {
        "status": "Processing started",
        "files": task_results,
        "total_files": len(task_results)
    }


@app.post("/query")
async def query_document(request: QueryRequest):
    """Query the Chunks with the vector embedding to find the most relevant chunks, and complete the RAG pipeline with streaming"""
    db = None
    try:
        queryVector = model.encode([request.question])[0]
        db = SessionLocal()
        similar_chunks = db.query(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(queryVector)).limit(5).all()
        context = "\n\n".join([f"[Chunk {i+1}]: {chunk.content}" 
                               for i, chunk in enumerate(similar_chunks)])
        
        
        chat_history_text = ""
        if request.chat_history:
            chat_history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in request.chat_history[-20:]  
            ])
        
        prompt = SYSTEM_PROMPT.format(
            context=context, 
            query=request.question, 
            chat_history=chat_history_text or "No previous conversation"
        )
        
        async def generate():
            try:
                
                response_stream = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    ),
                )
                
                
                for chunk in response_stream:
                    if chunk.text:
                        yield f"data: {chunk.text}\n\n"
                
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return {"error": str(e)}
    finally:
        if db is not None:
            db.close()