# app/schemas/documents_catalogs.py
from __future__ import annotations
from pydantic import BaseModel

# Tipos de documento
class TipoDocumentoOut(BaseModel):
    TipoID: int
    Nombre: str
    class Config:
        orm_mode = True

# Clasificaciones
class ClasificacionOut(BaseModel):
    ClasificacionID: int
    Nombre: str
    class Config:
        orm_mode = True

# Áreas
class AreaOut(BaseModel):
    AreaID: int
    Nombre: str
    class Config:
        orm_mode = True

# Usuarios
class UsuarioOut(BaseModel):
    UsuarioID: int
    Nombre: str
    Correo: str
    class Config:
        orm_mode = True
