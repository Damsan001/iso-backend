from __future__ import annotations
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.infrastructure.db import get_db
from app.infrastructure.models import Activo, Catalog, CatalogItem
from app.schemas.assets import (
    ActivoCreate, ActivoUpdate,
    ActivoDetailOut, ActivoListItemOut
)
from app.services.assets_service import create_asset, list_assets, search_assets, update_asset, delete_asset
from app.services.auth_service import get_current_user

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter(prefix="/assets", tags=["Activos"])

def _resolve_empresa_id(request: Request, q_empresa_id: Optional[int] = None) -> int:
    if q_empresa_id and q_empresa_id > 0:
        return int(q_empresa_id)
    hdr = request.headers.get("x-company-id")
    if hdr and hdr.isdigit():
        return int(hdr)
    return 1

def _ensure_item_belongs_to(db: Session, item_id: Optional[int], catalog_key: str, empresa_id: int) -> None:
    if item_id is None:
        return
    exists = (
        db.query(CatalogItem)
        .join(Catalog, Catalog.catalog_id == CatalogItem.catalog_id)
        .filter(Catalog.catalog_key == catalog_key)
        .filter(CatalogItem.active.is_(True))
        .filter(CatalogItem.deleted_at.is_(None))
        .filter(or_(CatalogItem.empresa_id == None, CatalogItem.empresa_id == empresa_id))
        .filter(CatalogItem.item_id == item_id)
        .first()
    )
    if not exists:
        raise HTTPException(status_code=400, detail=f"El item {item_id} no pertenece al catálogo '{catalog_key}' o no está disponible para la empresa.")

@router.get("", response_model=List[ActivoListItemOut])
def listar_activos(db: db_dependency, user: user_dependency):
    rows = list_assets(db, user)
    return rows

@router.get("/{activo_id}", response_model=ActivoDetailOut)
def obtener_activo(db: db_dependency, user: user_dependency,activo_id: int):
    row = search_assets(db, user, activo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return ActivoDetailOut.model_validate(row)

@router.post("", response_model=ActivoDetailOut)
def crear_activo(payload: ActivoCreate, db: db_dependency, user: user_dependency):
    asset = create_asset(payload, db, user)
    return asset


@router.patch("/{activo_id}", response_model=ActivoDetailOut)
def actualizar_activo(db: db_dependency, user: user_dependency,activo_id: int, payload: ActivoUpdate):
    row = update_asset(db, user,  activo_id, payload)
    return row

@router.delete("/{activo_id}", status_code=204)
def eliminar_activo(activo_id: int, db: Session = Depends(get_db)):
    delete_asset(db,user, activo_id)
    return
