from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class _ExtraIgnore(BaseModel):
    model_config = ConfigDict(extra="ignore")

# ====== Create / Update ======
class TratamientoCreate(_ExtraIgnore):
    TipoPlan: str = Field(..., pattern="^(mitigar|aceptar|transferir|eliminar)$")
    ResponsableID: Optional[int] = None
    FechaCompromiso: Optional[str] = None  # ISO datetime
    Efectividad: Optional[int] = Field(None, ge=1, le=3)
    Estatus: Optional[str] = Field("en_proceso")

class TratamientoUpdate(_ExtraIgnore):
    TipoPlan: Optional[str] = Field(None, pattern="^(mitigar|aceptar|transferir|eliminar)$")
    ResponsableID: Optional[int] = None
    FechaCompromiso: Optional[str] = None
    Efectividad: Optional[int] = Field(None, ge=1, le=3)
    Estatus: Optional[str] = None
    JustificacionCambioFecha: Optional[str] = None
    AprobadorCambioFechaID: Optional[int] = None

# ====== Out ======
class TratamientoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    tratamiento_id: int
    empresa_id: int
    riesgo_id: int
    tipo_plan: str
    responsable_id: Optional[int] = None
    fecha_compromiso: Optional[str] = None
    estatus: str
    score_inicial: Optional[int] = None
    efectividad: Optional[int] = None
    residual_score: Optional[int] = None
    residual_color: Optional[str] = None

class TratamientoListPage(BaseModel):
    items: List[TratamientoOut]
    total: int

# ====== Controles ======
class TratamientoControlCreate(_ExtraIgnore):
    TipoControl: str = Field(..., pattern="^(ISO|CI)$")
    ControlCode: str
    ControlName: str
    Observaciones: Optional[str] = None
    Activo: Optional[bool] = True

class TratamientoControlOut(BaseModel):
    tcontrol_id: int
    tratamiento_id: int
    tipo_control: str
    control_code: str
    control_name: str
    observaciones: Optional[str] = None
    activo: bool

# ====== Seguimientos ======
class TratamientoSeguimientoCreate(_ExtraIgnore):
    ResponsableID: Optional[int] = None
    Fecha: Optional[str] = None
    Comentario: Optional[str] = None
    Estatus: Optional[str] = None

class TratamientoSeguimientoOut(BaseModel):
    tseguimiento_id: int
    tratamiento_id: int
    responsable_id: Optional[int] = None
    fecha: str
    comentario: Optional[str] = None
    estatus: Optional[str] = None

# ====== Evidencias ======
class TratamientoEvidenciaCreate(_ExtraIgnore):
    Titulo: str
    Descripcion: Optional[str] = None
    Url: Optional[str] = None

class TratamientoEvidenciaOut(BaseModel):
    tevidencia_id: int
    tratamiento_id: int
    titulo: str
    descripcion: Optional[str] = None
    url: Optional[str] = None
    created_at: str

# ====== Carta de aceptación ======
class CartaAceptacionCreate(_ExtraIgnore):
    Justificacion: Optional[str] = None

class CartaAceptacionOut(BaseModel):
    carta_id: int
    tratamiento_id: int
    requiere_dg: bool
    firmada_dg: bool
    firmada_propietario: bool
    justificacion: Optional[str] = None
    documento_url: Optional[str] = None
    created_at: str
