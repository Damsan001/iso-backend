from pydantic import BaseModel

class ResponsibleAssignment(BaseModel):
    author: str
    reviewer: str
    approver: str
    comments: str | None = None
