from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.report import AuditFilter
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reportes"])


@router.post(
    "/audit",
    response_class=StreamingResponse,
    summary="Genera el Excel de auditoría según filtros",
)
def audit_report_excel(filters: AuditFilter):
    """
    Recibe filtros (date_from, date_to, types[], areas[], version_state)
    y devuelve un .xlsx listo para descargar.
    """
    excel_io = ReportService.generate_audit_report_excel(filters)
    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="audit_report.xlsx"'},
    )
