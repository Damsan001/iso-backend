from fastapi import UploadFile, HTTPException
from app.schemas.document import DocumentCreate, Document
from app.infrastructure.document_repository import DocumentRepository
from app.services.storage_service import LocalStorageService

storage = LocalStorageService()

class DocumentService:
    @staticmethod
    async def create_document(data: DocumentCreate, file: UploadFile) -> Document:
        # validar tipo de archivo
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

        # generar código: primeras 3 letras del valor de `type`, en mayúsculas, y next_id
        prefix = data.type.value[:3].upper()
        next_id = DocumentRepository.get_next_version(data.name, data.type)
        code_number = DocumentRepository.get_next_id(data.type)    
        code = f"{prefix}-{code_number:03d}"
        next_id=str(next_id)

        # guardar en disco
        
        await storage.save_file(file, code)

        # crear registro en "BD"
        return DocumentRepository.create_document(data, code, next_id)



# class DocumentService:
#     @staticmethod
#     def create_document(data: DocumentCreate) -> Document:
#         # validaciones adicionales aquí...
#         return DocumentRepository.create_document(data)

#     @staticmethod
#     def assign_responsibles(doc_id: int, assignment: ResponsibleAssignment) -> None:
#         # validar unicidad de usuarios...
#         # en repo real, guardar responsables
#         pass

#     @staticmethod
#     def review_document(doc_id: int, review: ReviewRequest) -> None:
#         # en repo real: registrar comentario, estado
#         pass

#     @staticmethod
#     def add_version(doc_id: int, version: VersionCreate) -> VersionInfo:
#         # comprobar permiso de gestor...
#         doc = DocumentRepository.get_document(doc_id)
#         return DocumentRepository.add_version(
#             doc_id,
#             version=doc.version,  # o nueva versión en datos de UI
#             description=version.description,
#             justification=version.justification,
#             requested_by=version.requested_by
#         )

#     @staticmethod
#     def get_version_history(doc_id: int) -> List[VersionInfo]:
#         return DocumentRepository.get_versions(doc_id)

#     @staticmethod
#     def list_visible_documents(role: str, classification: str) -> List[Document]:
#         return DocumentRepository.list_documents(role, classification)

#     @staticmethod
#     def get_document(doc_id: int) -> Document:
#         return DocumentRepository.get_document(doc_id)

#     @staticmethod
#     def export_documents(role: str, classification: str, fmt: str) -> bytes:
#         # Aquí generarías CSV o XLSX con pandas
#         return b""  # dummy
