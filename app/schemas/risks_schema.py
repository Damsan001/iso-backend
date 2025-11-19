from __future__ import annotations
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class _ExtraIgnore(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ======== GENERALES ========
class RiesgoGeneralCreate(_ExtraIgnore):
    Nombre: str = Field(..., min_length=1, max_length=200)
    Descripcion: Optional[str] = None
    ResponsableID: Optional[int] = None
    ProbabilidadID: Optional[int] = None
    ImpactoID: Optional[int] = None
    NivelID: Optional[int] = None
    Score: Optional[int] = None
    IntegridadID: Optional[int] = None
    DisponibilidadID: Optional[int] = None
    ConfidencialidadID: Optional[int] = None


class RiesgoGeneralUpdate(_ExtraIgnore):
    Nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    Descripcion: Optional[str] = None
    ResponsableID: Optional[int] = None
    ProbabilidadID: Optional[int] = None
    ImpactoID: Optional[int] = None
    NivelID: Optional[int] = None
    Score: Optional[int] = None
    IntegridadID: Optional[int] = None
    DisponibilidadID: Optional[int] = None
    ConfidencialidadID: Optional[int] = None


class RiesgoGeneralOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    riesgo_id: int
    empresa_id: int
    tipo_riesgo: str
    nombre: str
    descripcion: Optional[str] = None
    # extras (inyectados desde service)
    responsable_id: Optional[int] = 0
    probabilidad_item_id: Optional[int] = 0
    impacto_item_id: Optional[int] = 0
    nivel_item_id: Optional[int] = 0
    score: Optional[int] = None
    integridad_item_id: Optional[int] = 0
    disponibilidad_item_id: Optional[int] = 0
    confidencialidad_item_id: Optional[int] = 0


class RiesgoGeneralListPage(BaseModel):
    items: List[RiesgoGeneralOut]
    total: int


# ======== CON ACTIVO ========
class RiesgoActivoCreate(_ExtraIgnore):
    Nombre: str
    Descripcion: Optional[str] = None
    # soporte legacy (uno solo)
    ActivoID: Optional[int] = None
    AmenazaID: Optional[int] = None
    Vulnerabilidad: Optional[str] = None
    PropietarioID: Optional[int] = None
    Score: Optional[int] = None
    # prob/impact/nivel: directos (para activos != IND/INF/SOF)
    ProbabilidadID: Optional[int] = Field(None, alias="probabilidad_item_id")
    ImpactoID: Optional[int] = Field(None, alias="impacto_item_id")
    NivelID: Optional[int] = Field(None, alias="nivel_item_id")
    IntegridadID: Optional[int] = Field(None, alias="integridad_item_id")
    DisponibilidadID: Optional[int] = Field(None, alias="disponibilidad_item_id")
    ConfidencialidadID: Optional[int] = Field(None, alias="confidencialidad_item_id")


class RiesgoActivoUpdate(RiesgoActivoCreate):
    Nombre: Optional[str] = None


class RiesgoActivoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    riesgo_id: int
    empresa_id: int
    tipo_riesgo: str
    nombre: str
    descripcion: Optional[str] = None
    # extras (inyectados desde service)
    activo_id: Optional[int] = 0
    amenaza_item_id: Optional[int] = 0
    vulnerabilidad: Optional[str] = None
    propietario_id: Optional[int] = 0
    probabilidad_item_id: Optional[int] = 0
    impacto_item_id: Optional[int] = 0
    nivel_item_id: Optional[int] = 0
    score: Optional[int] = None
    integridad_item_id: Optional[int] = 0
    disponibilidad_item_id: Optional[int] = 0
    confidencialidad_item_id: Optional[int] = 0


class RiesgoActivoListPage(BaseModel):
    items: List[RiesgoActivoOut]
    total: int


# ======== VISTAS ENRIQUECIDAS ========
class RiesgoGeneralViewOut(BaseModel):
    riesgo_id: int
    empresa_id: int
    nombre: str
    descripcion: Optional[str] = None
    created_at: str
    updated_at: str
    responsable_id: Optional[int] = None
    responsable_nombre: Optional[str] = None
    probabilidad_item_id: Optional[int] = None
    probabilidad_nombre: Optional[str] = None
    impacto_item_id: Optional[int] = None
    impacto_nombre: Optional[str] = None
    nivel_item_id: Optional[int] = None
    nivel_nombre: Optional[str] = None
    score: Optional[int] = None


class RiesgoActivoViewOut(BaseModel):
    riesgo_id: int
    empresa_id: int
    nombre: str
    descripcion: Optional[str] = None
    created_at: str
    updated_at: str
    vulnerabilidad: Optional[str] = None
    propietario_id: Optional[int] = None
    propietario_nombre: Optional[str] = None
    amenaza_item_id: Optional[int] = None
    amenaza_nombre: Optional[str] = None
    probabilidad_item_id: Optional[int] = None
    probabilidad_nombre: Optional[str] = None
    impacto_item_id: Optional[int] = None
    impacto_nombre: Optional[str] = None
    nivel_item_id: Optional[int] = None
    nivel_nombre: Optional[str] = None
    score: Optional[int] = None
    # viene de jsonb_agg(to_jsonb(a))
    activos: List[dict]
    integridad_item_id: Optional[int] = None
    integridad_nombre: Optional[str] = None
    disponibilidad_item_id: Optional[int] = None
    disponibilidad_nombre: Optional[str] = None
    confidencialidad_item_id: Optional[int] = None
    confidencialidad_nombre: Optional[str] = None


class CatalogItemOut(BaseModel):
    item_id: int
    code: Optional[str] = None
    name: str
    sort_order: Optional[int] = None


class CatalogResolveItemIn(BaseModel):
    key: str
    item_id: int


class CatalogResolveRequest(BaseModel):
    items: List[CatalogResolveItemIn]


class CatalogResolveResponse(BaseModel):
    # {"probabilidad": {"45": {item}}, "impacto": {...}}
    values: Dict[str, Dict[str, CatalogItemOut]]
