from typing import List, Optional
from sqlalchemy.orm import Session
from starlette import status

from app.infrastructure.models import Activo, Catalog, CatalogItem, Areas
from sqlalchemy import or_
from fastapi import HTTPException

from app.schemas.assets import ActivoCreate, ActivoUpdate
from app.services.auth_service import ensure_authenticated, ensure_user_roles


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

def create_asset(payload: ActivoCreate,db: Session, user: dict):
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    _ensure_item_belongs_to(db, payload.TipoID, "tipo_activo", user["empresa_id"])
    _ensure_item_belongs_to(db, payload.EstadoID, "estado_activo", user["empresa_id"])
    _ensure_item_belongs_to(db, payload.ClasificacionID, "clasificacion_activo", user["empresa_id"])

    row = Activo(
        empresa_id=user["empresa_id"],
        nombre=payload.Nombre.strip(),
        tipo_item_id=payload.TipoID,
        estado_item_id=payload.EstadoID,
        clasificacion_item_id=payload.ClasificacionID,
        area_item_id=user["area_id"],
        descripcion=payload.Descripcion,
        ubicacion=payload.Ubicacion,
        fecha_adquisicion=payload.FechaAdquisicion,
        valor=payload.Valor,
        numero_serie=payload.NumeroSerie,
        modelo=payload.Modelo,
        propietario_id=user["user_id"],
        marca=payload.Marca,

    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def list_assets(db: Session, user: dict) -> List[Activo]:
    ensure_authenticated(user)


    rows = db.query(Activo).filter(
        Activo.empresa_id == user["empresa_id"],
        Activo.area_item_id == user["area_id"],
        Activo.deleted_at.is_(None)
    ).order_by(Activo.activo_id.desc()).all()
    return rows

def search_assets(db: Session, user: dict, activo_id: int | None = None):
    ensure_authenticated(user)
    if activo_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="activo_id is required")

    rows = db.query(Activo).filter(
        Activo.empresa_id == user["empresa_id"],
        Activo.area_item_id == user["area_id"],
        (Activo.activo_id == activo_id),
        Activo.deleted_at.is_(None)
    ).order_by(Activo.activo_id.desc()).first()
    return rows

def update_asset(db: Session, user: dict, activo_id: int, payload:ActivoUpdate) -> Activo:
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    row = db.query(Activo).filter(Activo.activo_id == activo_id, Activo.deleted_at.is_(None)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Activo no encontrado")



    if payload.TipoID is not None:
        _ensure_item_belongs_to(db, payload.TipoID, "tipo_activo", user["empresa_id"])
        row.tipo_item_id = payload.TipoID
    if payload.EstadoID is not None:
        _ensure_item_belongs_to(db, payload.EstadoID, "estado_activo", user["empresa_id"])
        row.estado_item_id = payload.EstadoID
    if payload.ClasificacionID is not None:
        _ensure_item_belongs_to(db, payload.ClasificacionID, "clasificacion_activo", user["empresa_id"])
        row.clasificacion_item_id = payload.ClasificacionID
    if payload.AreaID is not None:
        if payload.AreaID == 0:
            row.area_item_id = None
        else:
            ensure_area_exists(db, payload.AreaID, user["empresa_id"])
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

def ensure_area_exists(db: Session, area_id: Optional[int], empresa_id: int) -> None:
    if area_id is None:
        return
    exists = (
        db.query(Areas)
        .filter(Areas.area_id == area_id)
        .filter(Areas.empresa_id == empresa_id)
        .filter(Areas.deleted_at.is_(None))
        .first()
    )
    if not exists:
        raise HTTPException(status_code=400, detail=f"El área {area_id} no existe o no está disponible para la empresa.")
def delete_asset(db: Session,user:dict, activo_id: int) -> None:
    ensure_authenticated(user)
    required_roles = ["Administrador", "Supervisor"]
    ensure_user_roles(user, required_roles)

    row = db.query(Activo).filter(Activo.activo_id == activo_id, Activo.deleted_at.is_(None)).first()
    if not row:
        return
    # Soft delete
    from datetime import datetime, timezone
    row.deleted_at = datetime.now(tz=timezone.utc)
    db.commit()