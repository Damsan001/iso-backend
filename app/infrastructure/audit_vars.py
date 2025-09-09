from contextvars import ContextVar
from typing import Optional


current_actor: ContextVar[Optional[str]] = ContextVar("current_actor", default=None)