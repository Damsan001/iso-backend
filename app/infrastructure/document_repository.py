# app/infrastructure/document_repository.py

import csv
from pathlib import Path
from datetime import date
from typing import List
from app.schemas.document import Document, DocumentCreate, TypeOfDocument, Classification

# Carpeta y archivo donde se guardarán los registros
BASE_DIR = Path("data")
CSV_FILE = BASE_DIR / "documents.csv"

class DocumentRepository:

    @classmethod
    def _ensure_storage(cls):
        """Crea la carpeta y el CSV con cabecera si no existen."""
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        if not CSV_FILE.exists():
            with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id",
                    "name",
                    "type",
                    "area_responsible",
                    "author",
                    "reviewer",
                    "approver",
                    "classification",
                    "created_at",
                    "code",
                    "version"
                ])

    @classmethod
    def get_next_id(cls, doc_type: TypeOfDocument) -> int:
        """Calcula el próximo ID como max(id) + 1 para un tipo de documento específico."""
        cls._ensure_storage()
        max_id = 0
        with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Solo consideramos documentos del mismo tipo
                    if row["type"] == doc_type.value:
                        rid = int(row["id"])
                        if rid > max_id:
                            max_id = rid
                except ValueError:
                    continue
        return max_id + 1
        
    @classmethod
    def get_next_version(cls, name: str, doc_type: TypeOfDocument) -> int:
        """Calcula la próxima versión para un documento con el mismo nombre y tipo.
        Si existe, incrementa en 1 la versión, si no, devuelve 1."""
        cls._ensure_storage()
        max_version = 0
        with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["name"] == name and row["type"] == doc_type.value:
                    try:
                        version = int(row["version"])
                        if version > max_version:
                            max_version = version
                    except ValueError:
                        continue
        return max_version + 1 if max_version > 0 else 1

    @classmethod
    def create_document(cls, data: DocumentCreate, code: str, next_id:str) -> Document:
        """
        Crea el registro en CSV y devuelve el objeto Document.
        version siempre "1".
        """
        cls._ensure_storage()
        new_id = cls.get_next_id(data.type)
        created = date.today()
        version = str(next_id)

        # Añadimos la fila al CSV
        with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                new_id,
                data.name,
                data.type.value,
                data.area_responsible,
                data.author,
                data.reviewer,
                data.approver,
                data.classification.value,
                created.isoformat(),
                code,
                version
            ])

        # Devolvemos el Pydantic model
        return Document(
            id=new_id,
            name=data.name,
            type=data.type,
            area_responsible=data.area_responsible,
            author=data.author,
            reviewer=data.reviewer,
            approver=data.approver,
            classification=data.classification,
            created_at=created,
            code=code,
            version=version
        )

    @classmethod
    def list_documents(cls) -> List[Document]:
        """Lee todo el CSV y devuelve la lista de Document."""
        cls._ensure_storage()
        docs: List[Document] = []

        with CSV_FILE.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                docs.append(Document(
                    id=int(row["id"]),
                    name=row["name"],
                    type=TypeOfDocument(row["type"]),
                    area_responsible=row["area_responsible"],
                    author=row["author"],
                    reviewer=row["reviewer"],
                    approver=row["approver"],
                    classification=Classification(row["classification"]),
                    created_at=date.fromisoformat(row["created_at"]),
                    code=row["code"],
                    version=row["version"]
                ))

        return docs
