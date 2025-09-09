# region Imports

from sqlalchemy import true
from sqlalchemy.orm import Session
from fastapi import  HTTPException, status
from app.infrastructure.models import Rol, Empresa
from app.services.auth_service import ensure_authenticated, ensure_user_roles
from app.schemas.Dtos.AdminDtos import RoleDTO, CreateRoleDTO


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

# region roles
def read_all_roles(db: Session, user: dict):
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    roles = db.query(Rol).filter(Rol.activo == True).all()
    return [RoleDTO.from_orm(r) for r in roles]


def read_role_by_name(db: Session, user: dict, role_name: str):
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    role = (db.query(Rol)
            .filter(Rol.nombre == role_name)
            .filter(Rol.activo == True)
            .first())
    if not role:
        return None
    return RoleDTO.from_orm(role)

def create_role_service(db: Session, user: dict, role_data: CreateRoleDTO):
    ensure_authenticated(user)
    required_roles = ["Administrador"]
    ensure_user_roles(user, required_roles)

    new_role = Rol(**role_data.dict())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return RoleDTO.from_orm(new_role)

def update_role_service(db: Session, user: dict, role_id: int, role_data: CreateRoleDTO):
    ensure_authenticated(user)
    required_roles = ["Administrador"]
    ensure_user_roles(user, required_roles)

    role = (db.query(Rol)
            .filter(Rol.rol_id == role_id)
            .first())
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    for key, value in role_data.dict().items():
        setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return RoleDTO.from_orm(role)

def delete_role_service(db: Session, user: dict, role_id: int):
    ensure_authenticated(user)
    required_roles = ["Administrador"]
    ensure_user_roles(user, required_roles)

    role = (db.query(Rol)
            .filter(Rol.rol_id == role_id)
            .first())
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    role.activo = False
    db.commit()
    return {"message": "Rol eliminado exitosamente"}

# endregion
