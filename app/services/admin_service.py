# region Imports


from fastapi import HTTPException
from sqlalchemy import true
from sqlalchemy.orm import Session
from starlette import status

from app.infrastructure.models import Rol, Empresa
from app.services.auth_service import ensure_authenticated, ensure_user_roles


# endregion

# region Roles
# def read_all_roles(db: Session, user: dict):
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
#     return roles


# endregion

# region Empresas
def read_all_empresas(db: Session, user: dict):
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    empresas = db.query(Empresa).all()
    return empresas


def search_empresas(db: Session, user: dict, empresa_id: int | None = None):
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)
    filters = []

    if empresa_id is not None:
        filters.append(Empresa.empresa_id == empresa_id)

    filters.append(Empresa.estatus == 'ACTIVA')

    condition = true() if not filters else None

    q = db.query(Empresa)
    if condition is not None:
        q = q.filter(condition)
    else:
        q = q.filter(*filters)

    return q.all()

# endregion
