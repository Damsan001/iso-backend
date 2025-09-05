from __future__ import annotations
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# --- Simple catalog item DTO ---
class CatalogoItemSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int = Field(alias="item_id")
    name: str = Field(alias="name")

# --- Inputs ---
class ActivoCreate(BaseModel):
    Nombre: str = Field(..., min_length=1, max_length=100)
    TipoID: int
    EstadoID: int
    ClasificacionID: Optional[int] = Field(default=None)
    # EmpresaID: int
    AreaID: Optional[int] = None
    PropietarioID: Optional[int] = None
    Descripcion: Optional[str] = None
    Ubicacion: Optional[str] = None
    FechaAdquisicion: Optional[date] = None
    Valor: Optional[Decimal] = None
    NumeroSerie: Optional[str] = None
    Modelo: Optional[str] = None
    Marca: Optional[str] = None

class ActivoUpdate(BaseModel):
    Nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    TipoID: Optional[int] = None
    EstadoID: Optional[int] = None
    ClasificacionID: Optional[int] = None
    AreaID: Optional[int] = None
    PropietarioID: Optional[int] = None
    Descripcion: Optional[str] = None
    Ubicacion: Optional[str] = None
    FechaAdquisicion: Optional[date] = None
    Valor: Optional[Decimal] = None
    NumeroSerie: Optional[str] = None
    Modelo: Optional[str] = None
    EmpresaID: Optional[int] = None

# --- Outputs ---
class ActivoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(alias="activo_id")
    Nombre: str = Field(alias="nombre")
    EmpresaID: int = Field(alias="empresa_id")

    Marca: Optional[str] = Field(default=None, alias="marca", serialization_alias="marca")

    TipoID: Optional[int] = Field(default=None, alias="tipo_item_id")
    EstadoID: Optional[int] = Field(default=None, alias="estado_item_id")
    ClasificacionID: Optional[int] = Field(default=None, alias="clasificacion_item_id")
    AreaID: Optional[int] = Field(default=None, alias="area_item_id")

    Descripcion: Optional[str] = Field(default=None, alias="descripcion")
    Ubicacion: Optional[str] = Field(default=None, alias="ubicacion")
    FechaAdquisicion: Optional[date] = Field(default=None, alias="fecha_adquisicion")
    Valor: Optional[Decimal] = Field(default=None, alias="valor")
    NumeroSerie: Optional[str] = Field(default=None, alias="numero_serie")
    Modelo: Optional[str] = Field(default=None, alias="modelo")

    Tipo: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="tipo", serialization_alias="Tipo")
    Estado: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="estado", serialization_alias="Estado")
    Clasificacion: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="clasificacion", serialization_alias="Clasificacion")
    Area: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="area", serialization_alias="Area")
    PropietarioID: Optional[int] = Field(default=None, alias="propietario_id", serialization_alias="PropietarioID")
    Propietario: Optional[UsuarioMinOut] = Field(default=None, validation_alias="propietario", serialization_alias="Propietario")



class ActivoDetailOut(ActivoOut):
    pass

class ActivoListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(alias="activo_id")
    Nombre: str = Field(alias="nombre")
    Marca: Optional[str] = Field(default=None, alias="marca")
    Descripcion: Optional[str] = Field(default=None, alias="descripcion")
    Valor: Optional[Decimal] = Field(default=None, alias="valor")
    Tipo: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="tipo", serialization_alias="Tipo")
    Estado: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="estado", serialization_alias="Estado")
    Clasificacion: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="clasificacion", serialization_alias="Clasificacion")
    Area: Optional[CatalogoItemSimple] = Field(default=None, validation_alias="area", serialization_alias="Area")
    PropietarioID: Optional[int] = Field(default=None, alias="propietario_id", serialization_alias="PropietarioID")
    Propietario: Optional[UsuarioMinOut] = Field(default=None, validation_alias="propietario", serialization_alias="Propietario")

class UsuarioMinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    usuario_id: int
    full_name: str
    email: str