from fastapi import APIRouter, UploadFile, File, Form
from app.schemas.document import (
    DocumentCreate, Document,
    TypeOfDocument, Classification
)
from app.services.document_service import DocumentService

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
    file: UploadFile = File(...)
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
        classification=classification
    )
    return await DocumentService.create_document(dto, file)


# from fastapi import APIRouter, HTTPException, Depends, Query
# from typing import List
# from app.schemas.document import DocumentCreate, Document
# from app.schemas.responsible import ResponsibleAssignment
# from app.schemas.review import ReviewRequest
# from app.schemas.version import VersionCreate, VersionInfo
# from app.schemas.export import ExportRequest, ExportFormat
# from app.services.document_service import DocumentService

# router = APIRouter()

# @router.post("/", response_model=Document)
# def create_document(doc: DocumentCreate):
#     return DocumentService.create_document(doc)

# @router.post("/{doc_id}/responsibles", status_code=204)
# def set_responsibles(doc_id: int, assignment: ResponsibleAssignment):
#     if not DocumentService.get_document(doc_id):
#         raise HTTPException(404, "Documento no encontrado")
#     DocumentService.assign_responsibles(doc_id, assignment)
#     return

# @router.post("/{doc_id}/review", status_code=204)
# def review_document(doc_id: int, review: ReviewRequest):
#     if not DocumentService.get_document(doc_id):
#         raise HTTPException(404, "Documento no encontrado")
#     if review.action == review.REQUEST_CHANGES and not review.comments:
#         raise HTTPException(400, "Debe indicar comentarios al solicitar cambios")
#     DocumentService.review_document(doc_id, review)
#     return

# @router.post("/{doc_id}/versions", response_model=VersionInfo)
# def add_version(doc_id: int, version: VersionCreate):
#     if not DocumentService.get_document(doc_id):
#         raise HTTPException(404, "Documento no encontrado")
#     return DocumentService.add_version(doc_id, version)

# @router.get("/{doc_id}/versions", response_model=List[VersionInfo])
# def get_versions(doc_id: int):
#     if not DocumentService.get_document(doc_id):
#         raise HTTPException(404, "Documento no encontrado")
#     return DocumentService.get_version_history(doc_id)

# @router.get("/", response_model=List[Document])
# def list_documents(
#     role: str = Query(..., description="Rol del usuario"),
#     classification: str = Query(..., description="Clasificación")
# ):
#     return DocumentService.list_visible_documents(role, classification)

# @router.get("/{doc_id}", response_model=Document)
# def get_document(doc_id: int):
#     doc = DocumentService.get_document(doc_id)
#     if not doc:
#         raise HTTPException(404, "Documento no encontrado")
#     return doc

# @router.post("/export", response_model=dict)
# def export_docs(req: ExportRequest, role: str = Query(...), classification: str = Query(...)):
#     data = DocumentService.export_documents(role, classification, req.format)
#     return {"file_bytes": data}  # Adaptar para streaming en producción
