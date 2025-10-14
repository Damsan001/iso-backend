from pydantic import BaseModel, Field
from datetime import date
from enum import Enum
from typing import List
from app.schemas.document import TypeOfDocument

class VersionState(str, Enum):
    ALL = "all"
    CURRENT = "current"
    OBSOLETE = "obsolete"

class AuditFilter(BaseModel):
    date_from: date = Field(..., description="Fecha de creación desde")
    date_to:   date = Field(..., description="Fecha de creación hasta")
    types:     List[TypeOfDocument] = Field([], description="Lista de tipos de documento")
    areas:     List[str] = Field([], description="Lista de áreas responsables")
    version_state: VersionState = Field(
        VersionState.ALL,
        description="Incluir todas, sólo versión vigente u obsoletas"
    )
