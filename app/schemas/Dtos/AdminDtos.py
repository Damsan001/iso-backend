from pydantic import BaseModel

class RoleDTO(BaseModel):
    rol_id: int
    empresa_id: int
    nombre: str
    descripcion: str

    class Config:
        from_attributes = True

class CreateRoleDTO(BaseModel):
    empresa_id: int
    nombre: str
    descripcion: str
    activo: bool = True