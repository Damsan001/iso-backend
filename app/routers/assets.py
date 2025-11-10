# app/routers/assets.py
from __future__ import annotations
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.infrastructure.db import get_db
from app.infrastructure.models import Usuario
from app.schemas.assets import (
    ActivoCreate,
    ActivoUpdate,
    ActivoDetailOut,
    ActivoListPage,
    UsuarioMinOut,  # <-- importa el DTO para el combo
)
from app.services.assets_service import (
    create_asset,
    search_assets,
    update_asset,
    delete_asset,
    list_assets_paged,
)
from app.services.auth_service import get_current_user


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# <<< MANTÉN prefijo /assets >>>
router = APIRouter(prefix="/assets", tags=["Activos"])


# --- NUEVO: lista de usuarios (propietarios) ---
@router.get(
    "/usuarios",
    response_model=list[UsuarioMinOut],
    tags=["Usuarios/propietarios"],
    summary="Listar usuarios para activos",
)
def listar_usuarios_para_activos(
    db: db_dependency,
    user: user_dependency,
    area_id: Optional[int] = Query(None, description="Filtrar por área (opcional)"),
    q: Optional[str] = Query(None, description="Búsqueda por nombre/apellido/email"),
):
    empresa_id = user["empresa_id"]

    query = db.query(Usuario).filter(Usuario.empresa_id == empresa_id)

    if area_id is not None:
        query = query.filter(Usuario.area_id == area_id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Usuario.first_name.ilike(like),
                Usuario.last_name.ilike(like),
                Usuario.email.ilike(like),
            )
        )

    rows = query.order_by(Usuario.first_name, Usuario.last_name).all()

    return [
        UsuarioMinOut(
            usuario_id=u.usuario_id,
            full_name=f"{u.first_name} {u.last_name}".strip(),
            email=u.email,
        )
        for u in rows
    ]


# --- Rutas de activos (deja estas igual; están bajo /assets) ---
@router.get("", response_model=ActivoListPage)
def listar_activos(
    db: db_dependency,
    user: user_dependency,
    q: Optional[str] = Query(None, description="Texto de búsqueda"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
):
    offset = (page - 1) * page_size
    items, total = list_assets_paged(db, user, q, page_size, offset)
    # FastAPI serializa ORM->DTO gracias a from_attributes
    return {"items": items, "total": total}


@router.get("/{activo_id}", response_model=ActivoDetailOut)
def obtener_activo(db: db_dependency, user: user_dependency, activo_id: int):
    row = search_assets(db, user, activo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return ActivoDetailOut.model_validate(row)


@router.post("", response_model=ActivoDetailOut)
def crear_activo(payload: ActivoCreate, db: db_dependency, user: user_dependency):
    return create_asset(payload, db, user)


@router.patch("/{activo_id}", response_model=ActivoDetailOut)
def actualizar_activo(
    db: db_dependency, user: user_dependency, activo_id: int, payload: ActivoUpdate
):
    return update_asset(db, user, activo_id, payload)


@router.delete("/{activo_id}", status_code=204)
def eliminar_activo(activo_id: int, db: db_dependency, user: user_dependency):
    delete_asset(db, user, activo_id)
