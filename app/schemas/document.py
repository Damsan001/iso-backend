from pydantic import BaseModel, Field
from datetime import date
from enum import Enum

class Classification(str, Enum):
    PUBLICA = "Pública"
    INTERNA = "Interna"
    CONFIDENCIAL = "Confidencial"

class DocumentCreate(BaseModel):
    name: str = Field(..., max_length=150)
    code: str  # validar formato externamente
    version: str
    area_responsible: str
    author: str
    reviewer: str
    approver: str
    classification: Classification

class Document(DocumentCreate):
    id: int
    created_at: date
