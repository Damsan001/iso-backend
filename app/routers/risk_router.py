from __future__ import annotations
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.infrastructure.db import get_db
from app.infrastructure.risks_infra import Catalog, CatalogItem
from app.schemas.risks_schema import (
    RiesgoGeneralCreate, RiesgoGeneralUpdate, RiesgoGeneralOut, RiesgoGeneralListPage,
    RiesgoActivoCreate,  RiesgoActivoUpdate,  RiesgoActivoOut,  RiesgoActivoListPage,
)
from app.services import risks_service as svc

from app.services.risks_service import get_catalog_item, resolve_catalog_values
from app.schemas.risks_schema import (
    CatalogItemOut, CatalogResolveRequest, CatalogResolveResponse
)

# app/routers/risk_catalog_router.py
from app.schemas.assets import CatalogoItemSimple  # DTO simple ya usado en catálogos
from app.services.auth_service import get_current_user

router = APIRouter()
db_dependency   = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict,    Depends(get_current_user)]
# ======== GENERALES ========
@router.get("/generales", response_model=RiesgoGeneralListPage)
def listar_riesgos_generales(db: db_dependency, user: user_dependency,
                             q: Optional[str] = Query(None),
                             page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    offset = (page - 1) * page_size
    items, total = svc.list_riesgos_generales_paged(db, user, q, page_size, offset)
    return {"items": items, "total": total}

@router.get("/generales/{riesgo_id}", response_model=RiesgoGeneralOut)
def obtener_riesgo_general(riesgo_id: int, db: db_dependency, user: user_dependency):
    row = svc.get_riesgo_general(db, user, riesgo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Riesgo no encontrado")
    return row

@router.post("/generales", response_model=RiesgoGeneralOut)
def crear_riesgo_general(payload: RiesgoGeneralCreate, db: db_dependency, user: user_dependency):
    return svc.create_riesgo_general(db, user, payload)

@router.patch("/generales/{riesgo_id}", response_model=RiesgoGeneralOut)
def actualizar_riesgo_general(riesgo_id: int, payload: RiesgoGeneralUpdate, db: db_dependency, user: user_dependency):
    return svc.update_riesgo_general(db, user, riesgo_id, payload)

@router.delete("/generales/{riesgo_id}", status_code=204)
def eliminar_riesgo_general(riesgo_id: int, db: db_dependency, user: user_dependency):
    svc.delete_riesgo_general(db, user, riesgo_id)


# ======== CON ACTIVO ========
@router.get("/activos", response_model=RiesgoActivoListPage)
def listar_riesgos_activos(db: db_dependency, user: user_dependency,
                           q: Optional[str] = Query(None),
                           page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    offset = (page - 1) * page_size
    items, total = svc.list_riesgos_activo_paged(db, user, q, page_size, offset)
    return {"items": items, "total": total}

@router.get("/activos/{riesgo_id}", response_model=RiesgoActivoOut)
def obtener_riesgo_activo(riesgo_id: int, db: db_dependency, user: user_dependency):
    row = svc.get_riesgo_activo(db, user, riesgo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Riesgo con activo no encontrado")
    return row

@router.post("/activos", response_model=RiesgoActivoOut)
def crear_riesgo_activo(payload: RiesgoActivoCreate, db: db_dependency, user: user_dependency):
    return svc.create_riesgo_activo(db, user, payload)

@router.patch("/activos/{riesgo_id}", response_model=RiesgoActivoOut)
def actualizar_riesgo_activo(riesgo_id: int, payload: RiesgoActivoUpdate, db: db_dependency, user: user_dependency):
    return svc.update_riesgo_activo(db, user, riesgo_id, payload)

@router.delete("/activos/{riesgo_id}", status_code=204)
def eliminar_riesgo_activo(riesgo_id: int, db: db_dependency, user: user_dependency):
    svc.delete_riesgo_activo(db, user, riesgo_id)


# ======== LISTADOS (VISTAS) ========
@router.get("/generales/view")
def listar_generales_view_ep(db: db_dependency, user: user_dependency,
                             q: Optional[str] = Query(None),
                             page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    offset = (page - 1) * page_size
    items, total = svc.list_generales_view(db, user, q, page_size, offset)
    return {"items": items, "total": total}

@router.get("/activos/view")
def listar_activos_view_ep(db: db_dependency, user: user_dependency,
                           q: Optional[str] = Query(None),
                           page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    offset = (page - 1) * page_size
    items, total = svc.list_activos_view(db, user, q, page_size, offset)
    return {"items": items, "total": total}
@router.get("/catalogos/{key}/{item_id}", response_model=CatalogItemOut)
def get_catalog_value(key: str, item_id: int, db: Session = Depends(get_db)):
    return get_catalog_item(db, key, item_id)

@router.post("/catalogos/resolve", response_model=CatalogResolveResponse)
def resolve_catalog(req: CatalogResolveRequest, db: Session = Depends(get_db)):
    values = resolve_catalog_values(db, [i.dict() for i in req.items])
    return {"values": {k: {str(i): v for i, v in d.items()} for k, d in values.items()}}



@router.get("/catalogos/probabilidad", response_model=list[CatalogoItemSimple], summary="Catálogo Probabilidad")
def catalogo_probabilidad(db: db_dependency, user: user_dependency):
    return svc.list_probabilidad(db, user)

@router.get("/catalogos/impacto", response_model=list[CatalogoItemSimple], summary="Catálogo Impacto")
def catalogo_impacto(db: db_dependency, user: user_dependency):
    return svc.list_impacto(db, user)

@router.get("/catalogos/nivel-riesgo", response_model=list[CatalogoItemSimple], summary="Catálogo Nivel de Riesgo")
def catalogo_nivel_riesgo(db: db_dependency, user: user_dependency):
    return svc.list_nivel_riesgo(db, user)

@router.get("/catalogos/amenaza", response_model=list[CatalogoItemSimple], summary="Catálogo Amenaza")
def catalogo_amenaza(db: db_dependency, user: user_dependency):
    return svc.list_amenaza(db, user)
