from __future__ import annotations
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.services.auth_service import get_current_user
from app.schemas.treatments_schema import (
    TratamientoCreate, TratamientoUpdate, TratamientoOut, TratamientoListPage,
    TratamientoControlCreate, TratamientoControlOut,
    TratamientoSeguimientoCreate, TratamientoSeguimientoOut,
    TratamientoEvidenciaCreate, TratamientoEvidenciaOut,
    CartaAceptacionCreate, CartaAceptacionOut,
)
from app.services import treatments_service as svc

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# ===== Catálogos =====
@router.get("/catalogos/plan")
def catalogo_plan(db: db_dependency, user: user_dependency):
    return svc.get_catalog_items(db, "treatment_plan")

@router.get("/catalogos/estatus")
def catalogo_estatus(db: db_dependency, user: user_dependency):
    return svc.get_catalog_items(db, "treatment_status")

@router.get("/catalogos/efectividad")
def catalogo_efectividad(db: db_dependency, user: user_dependency):
    return svc.get_catalog_items(db, "treatment_effectiveness")

# ===== Buscador de riesgos =====
@router.get("/riesgos/search")
def buscar_riesgos(q: str = "", limit: int = 20, db: db_dependency = None, user: user_dependency = None):
    return svc.search_risks_for_treatments(db, user, q, limit)

# ===== Listado / CRUD Tratamientos =====
@router.get("/", response_model=TratamientoListPage)
def listar_tratamientos(
    db: db_dependency,
    user: user_dependency,
    riesgo_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
):
    offset = (page - 1) * page_size
    items, total = svc.list_tratamientos_paged(db, user, riesgo_id, q, page_size, offset)
    return {"items": items, "total": total}

@router.get("/{tratamiento_id}", response_model=TratamientoOut)
def obtener_tratamiento(tratamiento_id: int, db: db_dependency, user: user_dependency):
    row = svc.get_tratamiento(db, user, tratamiento_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return row

@router.post("/riesgos/{riesgo_id}/tratamientos", response_model=TratamientoOut)
def crear_tratamiento(riesgo_id: int, payload: TratamientoCreate, db: db_dependency, user: user_dependency):
    return svc.create_tratamiento(db, user, riesgo_id, payload)

@router.patch("/{tratamiento_id}", response_model=TratamientoOut)
def actualizar_tratamiento(tratamiento_id: int, payload: TratamientoUpdate, db: db_dependency, user: user_dependency):
    return svc.update_tratamiento(db, user, tratamiento_id, payload)

@router.delete("/{tratamiento_id}", status_code=204)
def eliminar_tratamiento(tratamiento_id: int, db: db_dependency, user: user_dependency):
    svc.delete_tratamiento(db, user, tratamiento_id)

# ===== Controles =====
@router.post("/{tratamiento_id}/controles", response_model=TratamientoControlOut)
def agregar_control(tratamiento_id: int, payload: TratamientoControlCreate, db: db_dependency, user: user_dependency):
    return svc.add_control(db, user, tratamiento_id, payload)

@router.delete("/{tratamiento_id}/controles/{tcontrol_id}", status_code=204)
def quitar_control(tratamiento_id: int, tcontrol_id: int, db: db_dependency, user: user_dependency):
    svc.remove_control(db, user, tratamiento_id, tcontrol_id)

# ===== Seguimientos =====
@router.post("/{tratamiento_id}/seguimientos", response_model=TratamientoSeguimientoOut)
def agregar_seguimiento(tratamiento_id: int, payload: TratamientoSeguimientoCreate, db: db_dependency, user: user_dependency):
    return svc.add_seguimiento(db, user, tratamiento_id, payload)

@router.get("/{tratamiento_id}/seguimientos", response_model=list[TratamientoSeguimientoOut])
def listar_seguimientos(tratamiento_id: int, db: db_dependency, user: user_dependency):
    return svc.list_seguimientos(db, user, tratamiento_id)

# ===== Evidencias =====
@router.post("/{tratamiento_id}/evidencias", response_model=TratamientoEvidenciaOut)
def agregar_evidencia(tratamiento_id: int, payload: TratamientoEvidenciaCreate, db: db_dependency, user: user_dependency):
    return svc.add_evidencia(db, user, tratamiento_id, payload)

# ===== Carta de aceptación =====
@router.post("/{tratamiento_id}/carta-aceptacion", response_model=CartaAceptacionOut)
def generar_carta(tratamiento_id: int, payload: CartaAceptacionCreate, db: db_dependency, user: user_dependency):
    return svc.generar_carta_aceptacion(db, user, tratamiento_id, payload.Justificacion)
