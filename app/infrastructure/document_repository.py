import csv
from pathlib import Path
from datetime import date
from typing import List, Optional
#infraestructura/document_repository
from app.schemas.document import DocumentCreate, Document, TypeOfDocument, Classification

BASE_DIR = Path("data")
DOC_CSV = BASE_DIR / "documents.csv"

class DocumentRepository:

    @classmethod
    def _ensure_storage(cls):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        if not DOC_CSV.exists():
            with DOC_CSV.open("w", newline="", encoding="utf-8") as f:
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
    def exists(cls, name: str, doc_type: TypeOfDocument) -> bool:
        """Devuelve True si ya hay un documento con mismo name+type."""
        cls._ensure_storage()
        with DOC_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["name"] == name and row["type"] == doc_type.value:
                    return True
        return False

    @classmethod
    def get_next_id(cls, doc_type: TypeOfDocument) -> int:
        """
        Siguiente secuencia para el código:
        Si ya existe un nombre idéntico, NO avanza (debe versionar).
        """
        cls._ensure_storage()
        max_id = 0
        with DOC_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["type"] == doc_type.value:
                    rid = int(row["id"])
                    if rid > max_id:
                        max_id = rid
        return max_id + 1

    @classmethod
    def create_document(cls, data: DocumentCreate, code: str) -> Document:
        """
        Inserta versión 1 del documento.
        """
        cls._ensure_storage()
        new_id = cls.get_next_id(data.type)
        created = date.today()
        version = "1"

        with DOC_CSV.open("a", newline="", encoding="utf-8") as f:
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
    def get_document(cls, doc_id: str) -> Optional[Document]:
        """Recupera un documento por su ID (última versión registrada)."""
        cls._ensure_storage()
        with DOC_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["code"] == doc_id:
                    return Document(
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
                    )
        return None
    
    @classmethod
    def update_version(cls, code: str, new_version: str) -> None:
        """
        Actualiza el campo 'version' para el registro con id = doc_id
        en documents.csv.
        """
        cls._ensure_storage()
        # 1) Leer todo
        rows = []
        with DOC_CSV.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["code"] == code:
                    row["version"] = new_version
                rows.append(row)

        # 2) Reescribir CSV completo con la nueva versión
        with DOC_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # encabezados en el mismo orden
            writer.writerow([
                "id","name","type","area_responsible","author",
                "reviewer","approver","classification",
                "created_at","code","version"
            ])
            for row in rows:
                writer.writerow([
                    row["id"],
                    row["name"],
                    row["type"],
                    row["area_responsible"],
                    row["author"],
                    row["reviewer"],
                    row["approver"],
                    row["classification"],
                    row["created_at"],
                    row["code"],
                    row["version"]
                ])

    @classmethod
    def list_documents(
        cls,
        filter_type: TypeOfDocument | None = None,
        filter_area: str | None = None
    ) -> List[Document]:
        """
        Lee todos los documentos y aplica filtros si vienen.
        """
        cls._ensure_storage()
        results: List[Document] = []
        with DOC_CSV.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # filtro por tipo
                if filter_type and row["type"] != filter_type.value:
                    continue
                # filtro por área (case-insensitive, parcial)
                if filter_area and filter_area.lower() not in row["area_responsible"].lower():
                    continue
                # reconstruir modelo
                results.append(Document(
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
        return results
