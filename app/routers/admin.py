from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.infrastructure.db import get_db
from app.schemas.Dtos.AdminDtos import CreateRoleDTO
from app.services.admin_service import read_all_empresas, search_empresas, read_all_roles, read_role_by_name, create_role_service, update_role_service,delete_role_service
from app.services.auth_service import get_current_user
from app.utils.audit_context import audit_context
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
router = APIRouter(dependencies=[Depends(audit_context)])

#region Roles
@router.get("/roles", status_code=status.HTTP_200_OK)
async def get_roles(db: db_dependency, user: user_dependency):
    roles = read_all_roles(db, user)
    return roles

@router.get("/roles/{role_name}", status_code=status.HTTP_200_OK)
async def get_role_by_name(role_name: str, db: db_dependency, user: user_dependency):
    role = read_role_by_name(db, user, role_name)
    return role

@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(db: db_dependency, user: user_dependency,role_data: CreateRoleDTO):
    rol = create_role_service(db, user, role_data)
    return rol

@router.put("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def update_role(role_id: int, db: db_dependency, user: user_dependency, role_data: CreateRoleDTO):

    update_role_service(db, user, role_id, role_data)
    return {"message": f"Rol actualizado exitosamente"}

@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(role_id: int, db: db_dependency, user: user_dependency):
    delete_role_service(db, user, role_id)
    return {"message": f"Rol eliminado exitosamente"}

#endregion

#region Empresas
@router.get("/empresas", status_code=status.HTTP_200_OK)
async def get_empresas(db: db_dependency, user: user_dependency):
    empresas = read_all_empresas(db, user)
    return empresas

@router.get("/empresas/{empresa_id}", status_code=status.HTTP_200_OK)
async def get_empresa(empresa_id: int, db: db_dependency, user: user_dependency):
    empresa = search_empresas(db, user, empresa_id)
    return empresa

@router.post("/empresas", status_code=status.HTTP_201_CREATED)
async def create_empresa(db: db_dependency, user: user_dependency):

    return {"message": "Empresa creada exitosamente"}

#endregion