from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from app.infrastructure.db import get_db
from app.schemas.Dtos.AdminDtos import CreateRoleDTO, UpdateRoleDTO, CreatePermissionDTO, UpdatePermissionDTO
from app.services.admin_service import read_all_empresas, search_empresas, read_all_roles, read_role_by_name, \
    create_role_service, update_role_service, delete_role_service, patch_role_service, add_roles_to_user_service, \
    get_roles_by_user_service, remove_roles_from_user_service, get_permissions_by_role_service, read_all_permissions, \
    read_permission_by_name, create_permission_service, patch_permission_service, update_permission_service, \
    add_permissions_to_user_service, remove_permissions_from_user_service, get_permissions_by_user_service, \
    delete_permission_service, add_permissions_to_role_service, remove_permissions_from_role_service
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
async def update_role(role_id: int, db: db_dependency, user: user_dependency, role_data: UpdateRoleDTO):

    update_role_service(db, user, role_id, role_data)
    return {"message": f"Rol actualizado exitosamente"}

@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(role_id: int, db: db_dependency, user: user_dependency):
    delete_role_service(db, user, role_id)
    return {"message": f"Rol eliminado exitosamente"}

@router.patch("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def patch_role(role_id: int, db: db_dependency, user: user_dependency, role_data: UpdateRoleDTO):
    patch_role_service(db, user, role_id, role_data)
    return {"message": f"Rol actualizado exitosamente"}

@router.post("/roles/assign/{user_id}", status_code=status.HTTP_200_OK)
async def assign_roles_to_user(db: db_dependency, user: user_dependency, user_id: int, role_ids: list[int]):
    add_roles_to_user_service(db, user, user_id, role_ids)
    return {"message": f"Roles asignados al usuario exitosamente"}

@router.get("/roles/user/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_roles(user_id: int, db: db_dependency, user: user_dependency):
    roles = get_roles_by_user_service(db, user, user_id)
    return roles

@router.post("/roles/unassign/{user_id}", status_code=status.HTTP_200_OK)
async def unassign_roles_from_user(db: db_dependency, user: user_dependency, user_id: int, role_ids: list[int]):
    remove_roles_from_user_service(db, user, user_id, role_ids)
    return {"message": f"Roles removidos del usuario exitosamente"}

@router.get("/roles/{role_id}/permisos", status_code=status.HTTP_200_OK)
async def get_role_permissions(role_id: int, db: db_dependency, user: user_dependency):
    permisos = get_permissions_by_role_service(db, user, role_id)
    return permisos
#endregion

#region Permisos
@router.get("/permisos", status_code=status.HTTP_200_OK)
async def get_permisos(db: db_dependency, user: user_dependency):
    permisos = read_all_permissions(db, user)
    return permisos
@router.get("/permisos/{permiso_name}", status_code=status.HTTP_200_OK)
async def get_permiso_by_name(permiso_name: str, db: db_dependency, user: user_dependency):
    permiso = read_permission_by_name(db, user, permiso_name)
    return permiso

@router.post("/permisos", status_code=status.HTTP_201_CREATED)
async def create_permiso(db: db_dependency, user: user_dependency, permiso_data: CreatePermissionDTO):
    permiso = create_permission_service(db, user, permiso_data)
    return permiso

@router.put("/permisos/{permmiso_id}", status_code=status.HTTP_200_OK)
async def update_permiso(permmiso_id: int, db: db_dependency, user: user_dependency, permiso_data: UpdatePermissionDTO):
    update_permission_service(db, user, permmiso_id, permiso_data)
    return {"message": f"Permiso actualizado exitosamente"}

@router.patch('/permisos/{permiso_id}', status_code=status.HTTP_200_OK)
async def patch_permiso(permiso_id: int, db: db_dependency, user: user_dependency, permiso_data: UpdatePermissionDTO):
    patch_permission_service(db, user, permiso_id, permiso_data)
    return {"message": f"Permiso actualizado exitosamente"}

@router.delete("/permisos/{permiso_id}", status_code=status.HTTP_200_OK)
async def delete_permiso(permiso_id: int, db: db_dependency, user: user_dependency):
    delete_permission_service(db, user, permiso_id)
    return {"message": f"Permiso eliminado exitosamente"}

@router.post("/permisos/assign/{user_id}", status_code=status.HTTP_200_OK)
async def assign_permisos_to_user(db: db_dependency, user: user_dependency, user_id: int, permiso_ids: list[int]):
    add_permissions_to_user_service(db, user, user_id, permiso_ids)
    return {"message": f"Permisos asignados al usuario exitosamente"}

@router.post("/permisos/unassign/{user_id}", status_code=status.HTTP_200_OK)
async def unassign_permisos_from_user(db: db_dependency, user: user_dependency, user_id: int, permiso_ids: list[int]):
    remove_permissions_from_user_service(db, user, user_id, permiso_ids)
    return {"message": f"Permisos removidos del usuario exitosamente"}

@router.post("/permisos/assign/role/{role_id}", status_code=status.HTTP_200_OK)
async def assign_permisos_to_role(db: db_dependency, user: user_dependency, role_id: int, permiso_ids: list[int]):
    add_permissions_to_role_service(db, user, role_id, permiso_ids)
    return {"message": f"Permisos asignados al rol exitosamente"}

@router.post("/permisos/unassign/role/{role_id}", status_code=status.HTTP_200_OK)
async def unassign_permisos_from_role(db: db_dependency, user: user_dependency, role_id: int, permiso_ids: list[int]):
    remove_permissions_from_role_service(db, user, role_id, permiso_ids)
    return {"message": f"Permisos removidos del rol exitosamente"}

@router.get("/permisos/{user_id}/permiso", status_code=status.HTTP_200_OK)
async def get_user_permisos(user_id: int, db: db_dependency, user: user_dependency):
    permisos = get_permissions_by_user_service(db, user, user_id)
    return permisos




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


#endregion