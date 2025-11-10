# Archivo Routers/ Documents_Catalogs
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

# Reutilizamos la infraestructura y helper de catálogos
from app.infrastructure.assets import (
    SessionLocal,
    get_catalog_items,
)

# Reutilizamos un schema simple para ítems de catálogo
from app.schemas.assets import CatalogoItemSimple


router = APIRouter(prefix="/documentos/catalogo", tags=["Catálogos de Documentos"])


# ------------------------------
# Dependencia de sesión
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------
# Resolver empresa (header/query)
# ------------------------------
def _resolve_empresa_id(
    request: Request,
    query_empresa_id: Optional[int] = None,
    default: int = 1,
) -> int:
    """
    Reglas de resolución de empresa:
      1) query (?empresa_id=)
      2) header X-Company-Id
      3) default (1)
    """
    if query_empresa_id:
        return int(query_empresa_id)
    hdr = request.headers.get("x-company-id")
    if hdr and hdr.isdigit():
        return int(hdr)
    return default


# ============================================================
#                       ENDPOINTS
# ============================================================


@router.get("/tipos", response_model=List[CatalogoItemSimple])
def listar_tipos(
    request: Request,
    empresa_id: Optional[int] = Query(
        None, description="Empresa que solicita el catálogo"
    ),
    db: Session = Depends(get_db),
):
    """
    Devuelve el catálogo 'tipo_documento' (global + específico de empresa).
    """
    emp = _resolve_empresa_id(request, empresa_id)
    return get_catalog_items(db, "tipo_documento", emp)


@router.get("/clasificaciones", response_model=List[CatalogoItemSimple])
def listar_clasif_documento(
    request: Request,
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Devuelve el catálogo 'clasificacion_documento' (Pública/Interna/Confidencial/Restringida…).
    """
    emp = _resolve_empresa_id(request, empresa_id)
    return get_catalog_items(db, "clasificacion_documento", emp)


@router.get("/estados", response_model=List[CatalogoItemSimple])
def listar_estados_documento(
    request: Request,
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Devuelve el catálogo 'estado_documento' (Borrador/En revisión/Aprobado/Obsoleto…).
    """
    emp = _resolve_empresa_id(request, empresa_id)
    return get_catalog_items(db, "estado_documento", emp)


@router.get("/permisos", response_model=List[CatalogoItemSimple])
def listar_permisos_documento(
    request: Request,
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Devuelve el catálogo 'permiso_documento' (Leer/Editar/Aprobar…).
    """
    emp = _resolve_empresa_id(request, empresa_id)
    return get_catalog_items(db, "permiso_documento", emp)


@router.get("/areas", response_model=List[CatalogoItemSimple])
def listar_areas(
    request: Request,
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Devuelve el catálogo 'area' para documentos (área responsable).
    """
    emp = _resolve_empresa_id(request, empresa_id)
    return get_catalog_items(db, "area", emp)
