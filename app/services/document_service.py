from fastapi import UploadFile, HTTPException

from pathlib import Path
from app.schemas.document import DocumentCreate, Document
from app.schemas.version import VersionCreate, VersionInfo
from app.infrastructure.document_repository import DocumentRepository
from app.infrastructure.version_repository import VersionRepository
from app.services.storage_service import LocalStorageService
from app.schemas.document import TypeOfDocument
from app.utils.text_utils import clear_name
from typing import Optional
from sqlalchemy.orm import Session
from app.infrastructure.version_repository import VersionRepository
from app.services import document_google_service  
from app.services.document_google_service import view_document_service

from typing import Optional, Callable
from app.infrastructure.version_repository import VersionRepository
from app.services.document_google_service import view_document_service

storage = LocalStorageService()

class DocumentService:
    
    @staticmethod
    async def create_document(data: DocumentCreate, file: UploadFile) -> Document:
        # 1) Validar existencia
        if DocumentRepository.exists(data.name, data.type):
            raise HTTPException(
                status_code=400,
                detail="El documento ya existe. Para nuevas versiones, use el endpoint de versionado."
            )

        # 2) Validar PDF
        if file.content_type != "application/pdf":
            raise HTTPException(400, "Solo se permiten archivos PDF")

        # 3) Generar código y secuencia
        prefix = data.type.value[:3].upper()
        seq = DocumentRepository.get_next_id(data.type)
        code = f"{prefix}-{seq:03d}"

        # 4) Guardar archivo v1 y obtener ruta
        filename = f"{code}-v1"
        file_path = await storage.save_file(file, filename)

        # 5) Crear registro en documents.csv (versión 1)
        doc = DocumentRepository.create_document(data, code)

        # 6) Registrar versión inicial en document_versions.csv
        initial_version = VersionCreate(
            description="Versión inicial",
            justification="Creación del documento",
            requested_by=data.author
        )
        VersionRepository.create_version(
            doc_id=doc.code,
            version=1,
            data=initial_version,
            file_path=file_path
        )

        return doc

    @staticmethod
    async def add_version(
        code: str,
        version_data: VersionCreate,
        file: UploadFile
    ) -> VersionInfo:
        # 1) Verificar que exista el documento
        doc = DocumentRepository.get_document(code)
        if not doc:
            raise HTTPException(404, "Documento no encontrado")

        # 2) Validar PDF
        if file.content_type != "application/pdf":
            raise HTTPException(400, "Solo se permiten archivos PDF")

        # 3) Calcular siguiente versión
        next_v = VersionRepository.get_next_version_by_id(code)

        # 4) Guardar el PDF con sufijo -vN
        filename = f"{doc.code}-v{next_v}"
        file_path = await storage.save_file(file, filename)

        # 5) Registrar en document_versions.csv
        version_info = VersionRepository.create_version(
            code,
            next_v,
            version_data,
            file_path
        )

        # 6) **Actualizar** la versión en documents.csv
        DocumentRepository.update_version(code, str(next_v))

        return version_info

    @staticmethod
    def list_versions(doc_id: int) -> list[VersionInfo]:
        # Opción de validación de existencia:
        if not DocumentRepository.get_document(doc_id):
            raise HTTPException(404, "Documento no encontrado")
        return VersionRepository.list_versions(doc_id)

    @staticmethod
    def list_documents(
        filter_type: TypeOfDocument | None = None,
        filter_area: str | None = None
    ) -> list[Document]:
        """
        Devuelve los documentos que coincidan con los filtros dados.
        """
        return DocumentRepository.list_documents(filter_type, filter_area)
    
    @staticmethod
    def get_document(code: str) -> Document:
        """
        Recupera un documento por su código.
        Lanza 404 si no existe el documento.
        """
        doc = DocumentRepository.get_document(code)
        if not doc:
            raise HTTPException(404, "Documento no encontrado")
        return doc

    @staticmethod
    
    def get_latest_file_path(code: str) -> Path:
        """
        Recupera la ruta al PDF de la versión actual del documento.
        Lanza 404 si no existe el documento.
        """
        doc = DocumentRepository.get_document(code)
        if not doc:
            raise HTTPException(404, "Documento no encontrado")
        return storage.get_file_path(doc.code, doc.version)
    
    async def get_signed_view_url(self, version_id: int, db: Session) -> Optional[str]:
        
        if not version_id:
            # Si no hay versión, devolvemos 404 claro
            raise HTTPException(
                status_code=404,
                detail="No se encontró una versión para este documento"
            )

        # Reutiliza tu servicio que ya funciona con version_id
        url = view_document_service(db, version_id)

        if not url:
            raise HTTPException(
                status_code=404,
                detail="No se pudo generar la URL firmada para la versión actual"
            )

        return url