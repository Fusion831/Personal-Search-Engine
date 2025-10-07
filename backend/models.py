from pydantic import BaseModel
from typing import List, Optional
from pgvector.sqlalchemy import Vector 
from sqlalchemy import Column,Integer,String,Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class DocumentChunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    
