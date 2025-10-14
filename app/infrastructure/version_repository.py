import csv
from pathlib import Path
from datetime import datetime
from typing import List

from app.schemas.version import VersionCreate, VersionInfo

BASE_DIR = Path("data")
VERS_CSV = BASE_DIR / "document_versions.csv"

class VersionRepository:

    @classmethod
    def _ensure_storage(cls):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        if not VERS_CSV.exists():
            with VERS_CSV.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "document_id",
                    "version",
                    "description",
                    "justification",
                    "requested_by",
                    "file_path",
                    "created_at"
                ])

    @classmethod
    def get_next_version_by_id(cls, code: str) -> int:
        cls._ensure_storage()
        max_v = 0
        with VERS_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["document_id"] == code:
                    v = int(row["version"])
                    if v > max_v:
                        max_v = v
        return max_v + 1

    @classmethod
    def create_version(
        cls,
        doc_id: int,
        version: int,
        data: VersionCreate,
        file_path: str
    ) -> VersionInfo:
        cls._ensure_storage()
        now_iso = datetime.now().isoformat()

        # Escribimos la fila completa (incluimos requested_by para histórico)
        with VERS_CSV.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                doc_id,
                version,
                data.description,
                data.justification,
                data.requested_by,
                file_path,
                now_iso
            ])

        # Devolvemos solo lo que pide el schema VersionInfo
        return VersionInfo(
            version=str(version),
            changed_at=datetime.fromisoformat(now_iso),
            description=data.description,
            justification=data.justification,
            requested_by=data.requested_by
        )

    @classmethod
    def list_versions(cls, code: str) -> List[VersionInfo]:
        cls._ensure_storage()
        results: List[VersionInfo] = []
        with VERS_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["document_id"]    == code:
                    results.append(VersionInfo(
                        version=row["version"],
                        changed_at=datetime.fromisoformat(row["created_at"]),
                        description=row["description"],
                        justification=row["justification"],
                        requested_by=row["requested_by"]
                    ))
        return results
