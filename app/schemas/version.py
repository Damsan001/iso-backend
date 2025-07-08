from pydantic import BaseModel
from datetime import datetime

class VersionCreate(BaseModel):
    description: str
    justification: str
    requested_by: str

class VersionInfo(BaseModel):
    version: str
    changed_at: datetime
    description: str
    justification: str
    requested_by: str
