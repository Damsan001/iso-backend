from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.infrastructure.db import get_db
from app.infrastructure.models import Activo, Catalog, CatalogItem
from app.schemas.assets import (
    ActivoCreate, ActivoUpdate,
    ActivoDetailOut, ActivoListItemOut
)

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
def listar_activos(request: Request, empresa_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, empresa_id)
    rows = db.query(Activo).filter(Activo.empresa_id == emp, Activo.deleted_at.is_(None)).order_by(Activo.activo_id.desc()).all()
    return rows

@router.get("/{activo_id}", response_model=ActivoDetailOut)
def obtener_activo(activo_id: int, db: Session = Depends(get_db)):
    row = db.query(Activo).filter(Activo.activo_id == activo_id, Activo.deleted_at.is_(None)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return row

@router.post("", response_model=ActivoDetailOut)
def crear_activo(payload: ActivoCreate, request: Request, db: Session = Depends(get_db)):
    emp = _resolve_empresa_id(request, payload.EmpresaID)
    _ensure_item_belongs_to(db, payload.TipoID, "tipo_activo", emp)
    _ensure_item_belongs_to(db, payload.EstadoID, "estado_activo", emp)
    _ensure_item_belongs_to(db, payload.ClasificacionID, "clasificacion_activo", emp)
    _ensure_item_belongs_to(db, payload.AreaID, "area", emp)

    row = Activo(
        empresa_id=emp,
        nombre=payload.Nombre.strip(),
        tipo_item_id=payload.TipoID,
        estado_item_id=payload.EstadoID,
        clasificacion_item_id=payload.ClasificacionID,
        area_item_id=payload.AreaID,
        descripcion=payload.Descripcion,
        ubicacion=payload.Ubicacion,
        fecha_adquisicion=payload.FechaAdquisicion,
        valor=payload.Valor,
        numero_serie=payload.NumeroSerie,
        modelo=payload.Modelo,
      
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.patch("/{activo_id}", response_model=ActivoDetailOut)
def actualizar_activo(activo_id: int, payload: ActivoUpdate, db: Session = Depends(get_db)):
    row = db.query(Activo).filter(Activo.activo_id == activo_id, Activo.deleted_at.is_(None)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    emp = row.empresa_id

    if payload.TipoID is not None:
        _ensure_item_belongs_to(db, payload.TipoID, "tipo_activo", emp)
        row.tipo_item_id = payload.TipoID
    if payload.EstadoID is not None:
        _ensure_item_belongs_to(db, payload.EstadoID, "estado_activo", emp)
        row.estado_item_id = payload.EstadoID
    if payload.ClasificacionID is not None:
        _ensure_item_belongs_to(db, payload.ClasificacionID, "clasificacion_activo", emp)
        row.clasificacion_item_id = payload.ClasificacionID
    if payload.AreaID is not None:
        if payload.AreaID == 0:
            row.area_item_id = None
        else:
            _ensure_item_belongs_to(db, payload.AreaID, "area", emp)
            row.area_item_id = payload.AreaID

    if payload.Nombre is not None:
        row.nombre = payload.Nombre.strip()
    if payload.Descripcion is not None:
        row.descripcion = payload.Descripcion
    if payload.Ubicacion is not None:
        row.ubicacion = payload.Ubicacion
    if payload.FechaAdquisicion is not None:
        row.fecha_adquisicion = payload.FechaAdquisicion
    if payload.Valor is not None:
        row.valor = payload.Valor
    if payload.NumeroSerie is not None:
        row.numero_serie = payload.NumeroSerie
    if payload.Modelo is not None:
        row.modelo = payload.Modelo

    db.commit()
    db.refresh(row)
    return row

@router.delete("/{activo_id}", status_code=204)
def eliminar_activo(activo_id: int, db: Session = Depends(get_db)):
    row = db.query(Activo).filter(Activo.activo_id == activo_id, Activo.deleted_at.is_(None)).first()
    if not row:
        return
    # Soft delete
    from datetime import datetime, timezone
    row.deleted_at = datetime.now(tz=timezone.utc)
    db.commit()
    return
