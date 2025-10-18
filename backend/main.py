from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from transformers import GenerationConfig
import models
from worker import process_document, model
from database import engine, SessionLocal
from models import ChildChunk, QueryRequest,ParentChunk
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
        You are a world-class AI research assistant. Your task is to provide precise, factual answers based ONLY on the provided <retrieved_parent_context> and the ongoing <chat_history>.

        **Important:** The <retrieved_parent_context> is a larger text excerpt (like a full paragraph) provided because a smaller, more specific sentence or phrase within it was identified as highly relevant to the <user_question>. Your answer should leverage the full context of the parent excerpt but focus on directly addressing the user's specific query.
    </role>

    <retrieved_parent_context>
    ---
    {context} 
    ---
    </retrieved_parent_context>

    <user_question>
    {query}
    </user_question>

    <chat_history>
    ---
    {chat_history}
    ---
    </chat_history>

    <instructions>
        <analysis_steps>
            1.  Carefully read and understand the current <user_question>. Consider if it's a follow-up related to the <chat_history>.
            2.  Thoroughly analyze the <retrieved_parent_context>. **Identify the specific information within this larger context that most directly relates to the likely topic of the (unseen) child chunk that triggered this retrieval.**
            3.  Analyze the <chat_history> to understand the flow and context of the conversation. Identify relevant information from past turns.
            4.  Synthesize the relevant information from **both the <retrieved_parent_context> (focusing on the most relevant parts) and the <chat_history>** into a draft answer.
            5.  Ensure the answer is concise and directly addresses the user's current question, fitting naturally into the ongoing conversation.
            6.  Verify that every statement is supported by the <retrieved_parent_context> or clearly established facts from the <chat_history>.
        </analysis_steps>

        <formatting_rules>
            1. Use proper Markdown formatting for clarity and emphasis (bold, italics, lists, headers, blockquotes).
            2. Structure your answer clearly with paragraphs and proper spacing.
            3. Make the response natural and readable - DO NOT include any XML tags in your output.
            4. DO NOT include chunk references like [Chunk 1], [Chunk 2] in your response.
        </formatting_rules>

        <response_rules>
            1. Answer using ONLY information explicitly found in the <retrieved_parent_context> or clearly stated in the <chat_history>.
            2. If the answer cannot be found in the provided information, respond ONLY with: "I could not find an answer in the provided documents or conversation history."
            3. Be DETAILED and COMPREHENSIVE in your explanations, drawing from the full parent context where relevant.
            4. Provide a natural, conversational, and descriptive response without any tags or metadata.
            5. Aim for depth and clarity based *only* on the provided materials.
        </response_rules>
    </instructions>

    <output_format>
        Provide your answer directly in clean Markdown format without any XML tags, thinking process, or metadata. Give a detailed, well-elaborated response that thoroughly addresses the question within the conversational context, leveraging the full parent chunk provided.
    </output_format>
</prompt>"""


HyDe_Prompt = """Write a short paragraph that provides a direct and factual answer to the following question. Assume this answer is derived from a relevant document. Do not include any introductory phrases like \"Based on the document...\" or mention that this is a hypothetical answer.

Question: {question}"""

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
    logger.info(f"Received query request: question={request.question}, document_id={request.document_id}, chat_history={len(request.chat_history) if request.chat_history else 0} messages")
    db = None
    try:
        db = SessionLocal()
        transform_prompt = HyDe_Prompt.format(question=request.question)
        transformed_question = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=transform_prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        transformed_question_text = transformed_question.text
        if transformed_question_text:
            queryVector = model.encode([transformed_question_text])[0]
        else:
            queryVector = model.encode([request.question])[0]
        
        summary_query = db.query(models.SummaryChunks)
        if request.document_id is not None:
            summary_query = summary_query.filter(models.SummaryChunks.document_id == request.document_id)
        
        
        top_summary = summary_query.order_by(models.SummaryChunks.embedding.l2_distance(queryVector)).first()
        
        summary_distance = None
        if top_summary:
            
            import numpy as np
            summary_distance = np.linalg.norm(np.array(top_summary.embedding) - np.array(queryVector))
            logger.info(f"Top summary from document {top_summary.document_id} with L2 distance: {summary_distance:.4f}")
            logger.info(f"Summary preview: {top_summary.summary_text[:200]}...")
        else:
            logger.warning("No document summaries found")

        
        query = db.query(ChildChunk)
        if request.document_id is not None:
            
            query = query.join(ParentChunk, ChildChunk.parent_chunk_id == ParentChunk.id)\
                         .filter(ParentChunk.document_id == request.document_id)

        similar_chunks = query.order_by(ChildChunk.embedding.l2_distance(queryVector)).limit(8).all()
        logger.info(f"Found {len(similar_chunks)} similar child chunks")
        
        chunk_distance = None
        if similar_chunks:
            
            chunk_distance = np.linalg.norm(np.array(similar_chunks[0].embedding) - np.array(queryVector))
            logger.info(f"Top child chunk L2 distance: {chunk_distance:.4f}")
            logger.info(f"First chunk preview: {similar_chunks[0].content[:100]}...")
        
       
        ROUTING_THRESHOLD = 0.8  
        use_summary = False
        
        if summary_distance is not None and chunk_distance is not None:
            
            if summary_distance < (chunk_distance * ROUTING_THRESHOLD):
                use_summary = True
                logger.info(f"ROUTING DECISION: Using SUMMARY (broad question). Summary distance {summary_distance:.4f} < {chunk_distance * ROUTING_THRESHOLD:.4f}")
            else:
                logger.info(f"ROUTING DECISION: Using PARENT-CHILD (specific question). Summary distance {summary_distance:.4f} >= {chunk_distance * ROUTING_THRESHOLD:.4f}")
        elif summary_distance is not None:
            
            use_summary = True
            logger.info("ROUTING DECISION: Using SUMMARY (only summaries available)")
        else:
            logger.info("ROUTING DECISION: Using PARENT-CHILD (no summaries available)")
        
        
        if use_summary and top_summary:
            
            final_context = f"[Document Summary]:\n{top_summary.summary_text}"
            logger.info(f"Using summary context, length: {len(final_context)}")
        else:
            
            parentChunkIds = list(set([chunk.parent_chunk_id for chunk in similar_chunks]))
            logger.info(f"Found {len(parentChunkIds)} unique parent IDs from {len(similar_chunks)} child chunks")
            
            parentContexts = db.query(ParentChunk).filter(ParentChunk.id.in_(parentChunkIds)).all() if parentChunkIds else []
            parentContent = [parent.content for parent in parentContexts]
            logger.info(f"Retrieved {len(parentContexts)} unique parent chunks for context")
            
            if not similar_chunks:
                logger.warning("No chunks found! Database might be empty or query failed.")
            
            context = "\n\n".join([f"[Chunk {i+1}]: {chunk.content}" 
                                   for i, chunk in enumerate(similar_chunks)])
            
            parent_context = "\n\n".join([f"[Parent {i+1}]: {content}" 
                                           for i, content in enumerate(parentContent)])
            
            
            final_context = f"{context}\n\n--- BROADER CONTEXT ---\n\n{parent_context}"
            logger.info(f"Child context length: {len(context)}, Parent context length: {len(parent_context)}")
        
        logger.info(f"Final context length: {len(final_context)}")

        chat_history_text = ""
        if request.chat_history:
            chat_history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in request.chat_history[-20:]  
            ])
        
        prompt = SYSTEM_PROMPT.format(
            context=final_context, 
            query=request.question, 
            chat_history=chat_history_text or "No previous conversation"
        )
        
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"Context preview: {final_context[:200]}...")
        
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