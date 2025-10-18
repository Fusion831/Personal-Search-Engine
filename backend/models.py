from pydantic import BaseModel

from sqlalchemy import ForeignKey
from typing import List, Optional
from pgvector.sqlalchemy import Vector 
from sqlalchemy import Column,Integer,String,Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base




class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)


class ParentChunk(Base):
    __tablename__ = "parents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
class ChildChunk(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_chunk_id: Mapped[int] = mapped_column(Integer, ForeignKey("parents.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

class SummaryChunks(Base):
    __tablename__ = "Summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = None
    document_id: Optional[int] = None
    
