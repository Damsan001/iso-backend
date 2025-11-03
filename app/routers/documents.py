from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Annotated
from fastapi import Query
from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.schemas.Dtos.DocumentDtos import DocumentCreateDto
from app.schemas.document import (
    DocumentCreate, Document,
    TypeOfDocument, Classification
)
from fastapi.responses import FileResponse
from pathlib import Path
from app.schemas.version import VersionCreate, VersionInfo
from app.services.auth_service import get_current_user
from app.services.document_google_service import create_documents_service, get_documents_service
from app.services.document_service import DocumentService
from app.infrastructure.version_repository import VersionRepository
from app.utils.audit_context import audit_context

router = APIRouter(tags=["Documentos"],dependencies=[Depends(audit_context)])
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/", response_model=str)
async def create_document(
    db: db_dependency,
    user: user_dependency,
    name: str = Form(...),
    type: str = Form(...),
    area_responsible: str = Form(...),
    author: str = Form(...),
    reviewer: str = Form(...),
    approver: str = Form(...),
    classification: str = Form(...),
    file: UploadFile = File(...)
):
    document = DocumentCreateDto(
        nombre=name,
        tipo_item_id=type,
        area_responsable_item_id=area_responsible,
        creador_id=author,
        revisado_por_id=reviewer,
        aprobador_por_id=approver,
        clasificacion_item_id=classification
    )
    return  create_documents_service(db, user, document, file)

@router.get("/" )
def get_documents(db: db_dependency):
    documents = get_documents_service(db)
    return documents
