from pydantic import BaseModel
from typing import Optional


class RoleDTO(BaseModel):
    rol_id: int
    empresa_id: int
    nombre: str
    descripcion: str

    model_config = {"from_attributes": True}


class CreateRoleDTO(BaseModel):
    empresa_id: int
    nombre: str
    descripcion: str
    activo: bool = True

    model_config = {"from_attributes": True}


class UpdateRoleDTO(BaseModel):
    empresa_id: Optional[int] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

    model_config = {"from_attributes": True}


class PermissionDTO(BaseModel):
    permiso_id: int
    codigo: str
    nombre: str

    model_config = {"from_attributes": True}


class CreatePermissionDTO(BaseModel):
    empresa_id: int
    codigo: str
    nombre: str
    descripcion: str
    activo: bool = True

    model_config = {"from_attributes": True}


class UpdatePermissionDTO(BaseModel):
    empresa_id: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

    model_config = {"from_attributes": True}
