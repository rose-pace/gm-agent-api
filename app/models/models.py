from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class Query(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class Response(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None

class Document(BaseModel):
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None

class RAGResult(BaseModel):
    """Represents the result of a RAG query"""
    text: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)