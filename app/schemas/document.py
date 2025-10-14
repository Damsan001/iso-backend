from pydantic import BaseModel
from datetime import date
from enum import Enum

class TypeOfDocument(str, Enum):
    POLICY = "Política"
    PROCEDURE = "Procedimiento"

class Classification(str, Enum):
    PUBLICA = "Pública"
    INTERNA = "Interna"
    CONFIDENCIAL = "Confidencial"

class DocumentCreate(BaseModel):
    name: str
    type: TypeOfDocument
    area_responsible: str
    author: str
    reviewer: str
    approver: str
    classification: Classification

class Document(DocumentCreate):
    id: int
    created_at: date
    code: str
    version: str
