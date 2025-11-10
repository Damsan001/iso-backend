from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.services.auth_service import get_current_user
from app.infrastructure.audit_vars import current_actor  # <- cambia el import

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


async def audit_context(db: db_dependency, user: user_dependency):
    actor = user.get("id") or user.get("username") or user.get("email")
    token = current_actor.set(actor)
    db.info["actor"] = actor
    try:
        yield
    finally:
        current_actor.reset(token)
