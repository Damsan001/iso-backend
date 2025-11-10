from io import BytesIO
from typing import List
import pandas as pd

from app.schemas.report import AuditFilter, VersionState
from app.infrastructure.document_repository import DocumentRepository
from app.infrastructure.version_repository import VersionRepository

class ReportService:

    @staticmethod
    def generate_audit_report_excel(filters: AuditFilter) -> BytesIO:
        # 1) Cargo y filtro documentos
        docs = DocumentRepository.list_documents(None, None)
        def in_range(d): return filters.date_from <= d.created_at <= filters.date_to
        def type_ok(d): return not filters.types or d.type in filters.types
        def area_ok(d): return not filters.areas or d.area_responsible in filters.areas

        filtered = [d for d in docs if in_range(d) and type_ok(d) and area_ok(d)]

        # 2) Construyo filas según version_state
        rows = []
        for d in filtered:
            rows.append({
                "id": d.id,
                "code": d.code,
                "name": d.name,
                "type": d.type.value,
                "area": d.area_responsible,
                "version": d.version,
                "created_at": d.created_at.isoformat()
            })

        # 3) DataFrame y Excel
        df = pd.DataFrame(rows, columns=[
            "id","code","name","type","area","version","created_at"
        ])
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Auditoría")
        buffer.seek(0)
        return buffer
