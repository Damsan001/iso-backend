from enum import Enum
from pydantic import BaseModel


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"


class ExportRequest(BaseModel):
    format: ExportFormat
