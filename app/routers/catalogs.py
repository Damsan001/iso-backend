from __future__ import annotations
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.infrastructure.db import get_db
from app.infrastructure.models import Catalog, CatalogItem, Areas
from app.schemas.assets import CatalogoItemSimple
from app.services.auth_service import get_current_user


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
router = APIRouter(prefix="/catalogo", tags=["Catálogos de Activos"])

def _resolve_empresa_id(request: Request, q_empresa_id: Optional[int] = None) -> int:
    if q_empresa_id and q_empresa_id > 0:
        return int(q_empresa_id)
    hdr = request.headers.get("x-company-id")
    if hdr and hdr.isdigit():
        return int(hdr)
    return 1

def _get_catalog_items(db: Session, catalog_key: str, empresa_id: int):
    q = (
        db.query(CatalogItem)
        .join(Catalog, Catalog.catalog_id == CatalogItem.catalog_id)
        .filter(Catalog.catalog_key == catalog_key)
        .filter(CatalogItem.active.is_(True))
        .filter(CatalogItem.deleted_at.is_(None))
        .filter(or_(CatalogItem.empresa_id == None, CatalogItem.empresa_id == empresa_id))
        .order_by(CatalogItem.sort_order, CatalogItem.name)
    )
    return q.all()
@router.get("/catalogo_clasificacion_documentos", response_model=List[CatalogoItemSimple])
def catalogo_clasificacion_documentos(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    return _get_catalog_items(db, "clasificacion_documento", emp)


@router.get("/tipos-documentos", response_model=List[CatalogoItemSimple])
def catalogo_tipos_documentos(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    return _get_catalog_items(db, "tipo_documento", emp)

@router.get("/tipos-activo", response_model=List[CatalogoItemSimple])
def catalogo_tipos_activo(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    return _get_catalog_items(db, "tipo_activo", emp)

@router.get("/estatus", response_model=List[CatalogoItemSimple])
def catalogo_estatus_activo(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    return _get_catalog_items(db, "estado_activo", emp)

@router.get("/clasificaciones", response_model=List[CatalogoItemSimple])
def catalogo_clasificaciones_activo(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    return _get_catalog_items(db, "clasificacion_activo", emp)

@router.get("/areas", response_model=List[CatalogoItemSimple])
def catalogo_areas(db:db_dependency,user: user_dependency):
    areas = (
        db.query(Areas.area_id.label("id"), Areas.nombre.label("name"))
        .filter(Areas.empresa_id == user["empresa_id"])
        .filter(Areas.deleted_at.is_(None))
        .order_by(Areas.nombre)
        .all()
    )
    return [CatalogoItemSimple(id=a.id, name=a.name) for a in areas]
