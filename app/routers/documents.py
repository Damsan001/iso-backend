from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Annotated
from fastapi import Query
from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.schemas.Dtos.DocumentDtos import DocumentCreateDto, DocumentVersionDto, ComentarioRevisionDto
from app.schemas.document import (
    DocumentCreate, Document,
    TypeOfDocument, Classification
)
from fastapi.responses import FileResponse
from pathlib import Path
from app.schemas.version import VersionCreate, VersionInfo
from app.services.auth_service import get_current_user
from app.services.document_google_service import create_documents_service, get_documents_service, view_document_service, \
    create_document_version_service, get_document_by_id_service, create_comentario_revision_service, \
    get_comentarios_by_version_service
from app.services.document_service import DocumentService
from app.infrastructure.version_repository import VersionRepository
from app.utils.audit_context import audit_context

router = APIRouter(tags=["Documentos"], dependencies=[Depends(audit_context)])
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
        aprobado_por_id=approver,
        clasificacion_item_id=classification
    )
    return create_documents_service(db, user, document, file)


@router.get("/")
def get_documents(db: db_dependency, user: user_dependency):
    return get_documents_service(db, user)


@router.get("/{document_id}")
def get_document_by_id(db: db_dependency, document_id: int):
    document = get_document_by_id_service(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return document


# Obtener el documento por el id
@router.get("/view/{version_id}", response_model=str)
def view_document(db: db_dependency, version_id: int):
    return view_document_service(db, version_id)


@router.post("/versions/{code}", response_model=str)
async def create_document_version(
        code: str,
        db: db_dependency,
        user: user_dependency,
        author: str = Form(...),
        reviewer: str = Form(...),
        approver: str = Form(...),
        descripcion: str = Form(...),
        justificacion: str = Form(...),
        file: UploadFile = File(...)
):
    document = DocumentVersionDto(

        creador_id=author,
        revisado_por_id=reviewer,
        aprobador_por_id=approver,
        descripcion=descripcion,
        justificacion=justificacion

    )
    return create_document_version_service(db, user, code, document, file)


@router.post("/comentarios", response_model=str)
def create_comentario_revision(db: db_dependency, user: user_dependency, comentario_data: ComentarioRevisionDto):
    return create_comentario_revision_service(db, user, comentario_data)


@router.get("/comentarios/{version_id}", response_model=List[dict])
def get_comentarios_by_version(db: db_dependency, version_id: int):
    return get_comentarios_by_version_service(db, version_id)
