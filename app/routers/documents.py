from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from fastapi import Query
from typing import Optional
from app.schemas.document import (
    DocumentCreate,
    Document,
    TypeOfDocument,
    Classification,
)
from fastapi.responses import FileResponse
from pathlib import Path
from app.schemas.version import VersionCreate, VersionInfo
from app.services.document_service import DocumentService
from app.infrastructure.version_repository import VersionRepository

router = APIRouter(tags=["Documentos"])


@router.post("/", response_model=Document)
async def create_document(
    name: str = Form(...),
    type: TypeOfDocument = Form(...),
    area_responsible: str = Form(...),
    author: str = Form(...),
    reviewer: str = Form(...),
    approver: str = Form(...),
    classification: Classification = Form(...),
    file: UploadFile = File(...),
):
    """
    Crea un documento:
    - Guarda el PDF en /storage/<CODE>.pdf
    - Registra metadata en memoria (id, código, versión=1, fecha)
    """
    dto = DocumentCreate(
        name=name,
        type=type,
        area_responsible=area_responsible,
        author=author,
        reviewer=reviewer,
        approver=approver,
        classification=classification,
    )
    return await DocumentService.create_document(dto, file)


@router.post("/{code}/versions", response_model=VersionInfo)
async def create_version(
    code: str,
    description: str = Form(..., description="Descripción del cambio"),
    justification: str = Form(..., description="Justificación del cambio"),
    requested_by: str = Form(..., description="Usuario solicitante"),
    file: UploadFile = File(...),
):
    version_data = VersionCreate(
        description=description, justification=justification, requested_by=requested_by
    )
    return await DocumentService.add_version(code, version_data, file)


@router.get("/{code}/versions", response_model=List[VersionInfo])
def list_versions(code: str):
    # opcional: validar existencia de doc_id
    return VersionRepository.list_versions(code)


@router.get("/", response_model=List[Document])
def list_documents(
    type: Optional[TypeOfDocument] = Query(
        None, description="Filtrar por tipo de documento"
    ),
    area_responsible: Optional[str] = Query(
        None, description="Filtrar por área responsable (texto libre)"
    ),
):
    """
    Lista documentos; acepta filtros opcionales de tipo y área.
    """
    return DocumentService.list_documents(type, area_responsible)


@router.get("/{code}/view", response_class=FileResponse)
def download_document(code: str):
    """
    Devuelve el PDF de la versión actual para mostrar en línea.
    Solo usuarios con permiso 'view_document' podrán acceder.
    """
    # 1) Validar existencia y permisos
    doc = DocumentService.get_document(code)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    # if not current_user.has_permission("view_document", doc_id):
    #     raise HTTPException(403, "No tienes permiso para ver este documento")

    # 2) Obtener ruta al archivo
    file_path = DocumentService.get_latest_file_path(code)
    if not Path(file_path).exists():
        raise HTTPException(404, "Archivo no encontrado")

    # 3) Envío inline (no fuerza descarga)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{Path(file_path).name}"'},
    )
