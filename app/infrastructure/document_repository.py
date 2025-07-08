from typing import List
from app.schemas.document import Document, DocumentCreate
from app.schemas.version import VersionInfo
from datetime import date, datetime

# Dummy storage
_docs: List[Document] = []
_versions: dict[int, List[VersionInfo]] = {}
_id_counter = 1

class DocumentRepository:
    @classmethod
    def create_document(cls, data: DocumentCreate) -> Document:
        global _id_counter
        doc = Document(
            id=_id_counter,
            created_at=date.today(),
            **data.model_dump()
        )
        _docs.append(doc)
        _versions[doc.id] = []
        _id_counter += 1
        return doc

    @classmethod
    def get_document(cls, doc_id: int) -> Document | None:
        return next((d for d in _docs if d.id == doc_id), None)

    @classmethod
    def list_documents(cls, role: str, classification: str) -> List[Document]:
        # aquí podrías filtrar según role y clasificación
        return _docs

    @classmethod
    def add_version(cls, doc_id: int, version: str, description: str, justification: str, requested_by: str) -> VersionInfo:
        vi = VersionInfo(
            version=version,
            changed_at=datetime.now(),
            description=description,
            justification=justification,
            requested_by=requested_by
        )
        _versions[doc_id].append(vi)
        return vi

    @classmethod
    def get_versions(cls, doc_id: int) -> List[VersionInfo]:
        return _versions.get(doc_id, [])
