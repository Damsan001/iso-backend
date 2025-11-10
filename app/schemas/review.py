from pydantic import BaseModel
from enum import Enum


class ReviewAction(str, Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"


class ReviewRequest(BaseModel):
    action: ReviewAction
    comments: str | None = None
    reviewer: str
