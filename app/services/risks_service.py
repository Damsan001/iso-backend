from __future__ import annotations
from typing import Optional, List, Dict
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy import text


from app.infrastructure.risks_infra import (
    Riesgo,
    RiesgoGeneralExtra,
    RiesgoActivoExtra,
    RiesgoActivoRel,
    Catalog,
    CatalogItem,
    VRiesgoGeneralList,
    VRiesgoActivoList,
)
from app.services.auth_service import ensure_authenticated, ensure_user_roles
from app.infrastructure.models import CatalogItem

# ---------- Helpers Catálogo / Score (ORM) ----------
def _ensure_item_belongs_to(db: Session, item_id: int | None, key: str):
    if item_id is None:
        return None
    q = (
        db.query(CatalogItem.item_id, CatalogItem.sort_order)
        .join(Catalog, Catalog.catalog_id == CatalogItem.catalog_id)
        .filter(Catalog.catalog_key == key, CatalogItem.item_id == item_id)
    )
    row = q.first()
    if not row:
        raise HTTPException(
            status_code=400,
            detail=f"El item_id {item_id} no pertenece al catálogo '{key}'.",
        )
    return {"item_id": row.item_id, "sort_order": row.sort_order}


def _auto_score(prob: dict | None, imp: dict | None, default: int | None) -> int | None:
    if default is not None:
        return default
    if prob and imp:
        p = int(prob.get("sort_order") or 1)
        i = int(imp.get("sort_order") or 1)
        return p * i
    return None


# ---------- Base ----------
def _q_base(db: Session, empresa_id: int, tipo: str):
    return db.query(Riesgo).filter(
        Riesgo.empresa_id == empresa_id,
        Riesgo.tipo_riesgo == tipo,
        Riesgo.deleted_at.is_(None),
    )


# ========== GENERALES ==========
def create_riesgo_general(db: Session, user: dict, payload) -> Riesgo:
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])

    r = Riesgo(
        empresa_id=user["empresa_id"],
        tipo_riesgo="general",
        nombre=payload.Nombre.strip(),
        descripcion=payload.Descripcion,
    )
    db.add(r)
    db.flush()

    prob = _ensure_item_belongs_to(db, payload.ProbabilidadID, "probabilidad")
    imp = _ensure_item_belongs_to(db, payload.ImpactoID, "impacto")
    _ = _ensure_item_belongs_to(db, payload.NivelID, "nivel_riesgo")
    score = _auto_score(prob, imp, payload.Score)

    e = RiesgoGeneralExtra(
        riesgo_id=r.riesgo_id,
        responsable_id=payload.ResponsableID,
        probabilidad_item_id=payload.ProbabilidadID,
        impacto_item_id=payload.ImpactoID,
        nivel_item_id=payload.NivelID,
        score=score,
    )
    db.merge(e)
    db.commit()
    db.refresh(r)
    return r


def list_riesgos_generales_paged(
    db: Session, user: dict, q: Optional[str], limit: int, offset: int
):
    ensure_authenticated(user)
    base = _q_base(db, user["empresa_id"], "general")
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(
            or_(Riesgo.nombre.ilike(like), Riesgo.descripcion.ilike(like))
        )
    total = base.with_entities(func.count()).scalar() or 0
    items = base.order_by(Riesgo.riesgo_id.desc()).limit(limit).offset(offset).all()

    ids = [r.riesgo_id for r in items]
    if ids:
        ext = {
            e.riesgo_id: e
            for e in db.query(RiesgoGeneralExtra)
            .filter(RiesgoGeneralExtra.riesgo_id.in_(ids))
            .all()
        }
        for r in items:
            e = ext.get(r.riesgo_id)
            if e:
                r.responsable_id = e.responsable_id
                r.probabilidad_item_id = e.probabilidad_item_id
                r.impacto_item_id = e.impacto_item_id
                r.nivel_item_id = e.nivel_item_id
                r.score = e.score
    return items, total


def get_riesgo_general(db: Session, user: dict, riesgo_id: int):
    ensure_authenticated(user)
    r = (
        _q_base(db, user["empresa_id"], "general")
        .filter(Riesgo.riesgo_id == riesgo_id)
        .first()
    )
    if r:
        e = (
            db.query(RiesgoGeneralExtra)
            .filter(RiesgoGeneralExtra.riesgo_id == r.riesgo_id)
            .first()
        )
        if e:
            r.responsable_id = e.responsable_id
            r.probabilidad_item_id = e.probabilidad_item_id
            r.impacto_item_id = e.impacto_item_id
            r.nivel_item_id = e.nivel_item_id
            r.score = e.score
    return r


def update_riesgo_general(db: Session, user: dict, riesgo_id: int, payload):
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])
    r = (
        _q_base(db, user["empresa_id"], "general")
        .filter(Riesgo.riesgo_id == riesgo_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Riesgo no encontrado")

    if payload.Nombre is not None:
        r.nombre = payload.Nombre.strip()
    if payload.Descripcion is not None:
        r.descripcion = payload.Descripcion

    e = db.query(RiesgoGeneralExtra).filter(
        RiesgoGeneralExtra.riesgo_id == r.riesgo_id
    ).first() or RiesgoGeneralExtra(riesgo_id=r.riesgo_id)

    prob = (
        _ensure_item_belongs_to(db, payload.ProbabilidadID, "probabilidad")
        if payload.ProbabilidadID is not None
        else None
    )
    imp = (
        _ensure_item_belongs_to(db, payload.ImpactoID, "impacto")
        if payload.ImpactoID is not None
        else None
    )
    _ = (
        _ensure_item_belongs_to(db, payload.NivelID, "nivel_riesgo")
        if payload.NivelID is not None
        else None
    )

    if payload.ResponsableID is not None:
        e.responsable_id = payload.ResponsableID
    if payload.ProbabilidadID is not None:
        e.probabilidad_item_id = payload.ProbabilidadID
    if payload.ImpactoID is not None:
        e.impacto_item_id = payload.ImpactoID
    if payload.NivelID is not None:
        e.nivel_item_id = payload.NivelID
    if payload.IntegridadID is not None:
        e.integridad_item_id = payload.IntegridadID
    if payload.DisponibilidadID is not None:
        e.disponibilidad_item_id = payload.DisponibilidadID
    if payload.ConfidencialidadID is not None:
        e.confidencialidad_item_id = payload.ConfidencialidadID

    if payload.Score is not None:
        e.score = payload.Score
    else:
        cur_prob = prob or (
            {"sort_order": None}
            if e.probabilidad_item_id is None
            else _ensure_item_belongs_to(db, e.probabilidad_item_id, "probabilidad")
        )
        cur_imp = imp or (
            {"sort_order": None}
            if e.impacto_item_id is None
            else _ensure_item_belongs_to(db, e.impacto_item_id, "impacto")
        )
        e.score = _auto_score(cur_prob, cur_imp, None)

    db.merge(e)
    db.commit()
    db.refresh(r)
    return r


def delete_riesgo_general(db: Session, user: dict, riesgo_id: int):
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])
    r = (
        _q_base(db, user["empresa_id"], "general")
        .filter(Riesgo.riesgo_id == riesgo_id)
        .first()
    )
    if not r:
        return
    from datetime import datetime, timezone

    r.deleted_at = datetime.now(tz=timezone.utc)
    db.commit()


# ========== CON ACTIVO ==========
def _sync_activos_rel(db: Session, riesgo_id: int, activos: List[int] | None):
    if activos is None:
        return
    db.query(RiesgoActivoRel).filter(RiesgoActivoRel.riesgo_id == riesgo_id).delete()
    for aid in set(activos):
        db.add(RiesgoActivoRel(riesgo_id=riesgo_id, activo_id=aid))


def create_riesgo_activo(db: Session, user: dict, payload) -> Riesgo:
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])

    r = Riesgo(
        empresa_id=user["empresa_id"],
        tipo_riesgo="activo",
        nombre=payload.Nombre.strip(),
        descripcion=payload.Descripcion,
    )
    db.add(r)
    db.flush()

    _ = _ensure_item_belongs_to(db, payload.AmenazaID, "amenaza")
    prob = _ensure_item_belongs_to(db, payload.ProbabilidadID, "probabilidad")
    imp = _ensure_item_belongs_to(db, payload.ImpactoID, "impacto")
    _ = _ensure_item_belongs_to(db, payload.NivelID, "nivel_riesgo")
    score = _auto_score(prob, imp, payload.Score)

    e = RiesgoActivoExtra(
        riesgo_id=r.riesgo_id,
        activo_id=payload.ActivoID,
        amenaza_item_id=payload.AmenazaID,
        vulnerabilidad=payload.Vulnerabilidad,
        propietario_id=payload.PropietarioID,
        probabilidad_item_id=payload.ProbabilidadID,
        impacto_item_id=payload.ImpactoID,
        nivel_item_id=payload.NivelID,
        score=score,
        integridad_item_id=payload.IntegridadID,
        disponibilidad_item_id=payload.DisponibilidadID,
        confidencialidad_item_id=payload.ConfidencialidadID,
    )
    db.merge(e)

    activos = [payload.ActivoID] if payload.ActivoID else []
    _sync_activos_rel(db, r.riesgo_id, activos)

    db.commit()
    db.refresh(r)
    return r


def list_riesgos_activo_paged(
    db: Session, user: dict, q: Optional[str], limit: int, offset: int
):
    ensure_authenticated(user)
    base = _q_base(db, user["empresa_id"], "activo")
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(
            or_(Riesgo.nombre.ilike(like), Riesgo.descripcion.ilike(like))
        )
    total = base.with_entities(func.count()).scalar() or 0
    items = base.order_by(Riesgo.riesgo_id.desc()).limit(limit).offset(offset).all()

    ids = [r.riesgo_id for r in items]
    if ids:
        ext = {
            e.riesgo_id: e
            for e in db.query(RiesgoActivoExtra)
            .filter(RiesgoActivoExtra.riesgo_id.in_(ids))
            .all()
        }
        for r in items:
            e = ext.get(r.riesgo_id)
            if e:
                r.activo_id = e.activo_id
                r.amenaza_item_id = e.amenaza_item_id
                r.vulnerabilidad = e.vulnerabilidad
                r.propietario_id = e.propietario_id
                r.probabilidad_item_id = e.probabilidad_item_id
                r.impacto_item_id = e.impacto_item_id
                r.nivel_item_id = e.nivel_item_id
                r.score = e.score
                r.integridad_item_id = e.integridad_item_id
                r.disponibilidad_item_id = e.disponibilidad_item_id
                r.confidencialidad_item_id = e.confidencialidad_item_id
    return items, total


def get_riesgo_activo(db: Session, user: dict, riesgo_id: int):
    ensure_authenticated(user)
    r = (
        _q_base(db, user["empresa_id"], "activo")
        .filter(Riesgo.riesgo_id == riesgo_id)
        .first()
    )
    if r:
        e = (
            db.query(RiesgoActivoExtra)
            .filter(RiesgoActivoExtra.riesgo_id == r.riesgo_id)
            .first()
        )
        if e:
            r.activo_id = e.activo_id
            r.amenaza_item_id = e.amenaza_item_id
            r.vulnerabilidad = e.vulnerabilidad
            r.propietario_id = e.propietario_id
            r.probabilidad_item_id = e.probabilidad_item_id
            r.impacto_item_id = e.impacto_item_id
            r.nivel_item_id = e.nivel_item_id
            r.score = e.score
            r.integridad_item_id = e.integridad_item_id
            r.disponibilidad_item_id = e.disponibilidad_item_id
            r.confidencialidad_item_id = e.confidencialidad_item_id
    return r


def update_riesgo_activo(db: Session, user: dict, riesgo_id: int, payload):
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])
    r = (
        _q_base(db, user["empresa_id"], "activo")
        .filter(Riesgo.riesgo_id == riesgo_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Riesgo con activo no encontrado")

    if payload.Nombre is not None:
        r.nombre = payload.Nombre.strip()
    if payload.Descripcion is not None:
        r.descripcion = payload.Descripcion

    e = db.query(RiesgoActivoExtra).filter(
        RiesgoActivoExtra.riesgo_id == r.riesgo_id
    ).first() or RiesgoActivoExtra(riesgo_id=r.riesgo_id)

    _ = (
        _ensure_item_belongs_to(db, payload.AmenazaID, "amenaza")
        if payload.AmenazaID is not None
        else None
    )
    prob = (
        _ensure_item_belongs_to(db, payload.ProbabilidadID, "probabilidad")
        if payload.ProbabilidadID is not None
        else None
    )
    imp = (
        _ensure_item_belongs_to(db, payload.ImpactoID, "impacto")
        if payload.ImpactoID is not None
        else None
    )
    _ = (
        _ensure_item_belongs_to(db, payload.NivelID, "nivel_riesgo")
        if payload.NivelID is not None
        else None
    )

    if payload.ActivoID is not None:
        e.activo_id = payload.ActivoID
    if payload.AmenazaID is not None:
        e.amenaza_item_id = payload.AmenazaID
    if payload.Vulnerabilidad is not None:
        e.vulnerabilidad = payload.Vulnerabilidad
    if payload.PropietarioID is not None:
        e.propietario_id = payload.PropietarioID
    if payload.ProbabilidadID is not None:
        e.probabilidad_item_id = payload.ProbabilidadID
    if payload.ImpactoID is not None:
        e.impacto_item_id = payload.ImpactoID
    if payload.NivelID is not None:
        e.nivel_item_id = payload.NivelID
    if payload.IntegridadID is not None:
        e.integridad_item_id = payload.IntegridadID
    if payload.DisponibilidadID is not None:
        e.disponibilidad_item_id = payload.DisponibilidadID
    if payload.ConfidencialidadID is not None:
        e.confidencialidad_item_id = payload.ConfidencialidadID

    if payload.Score is not None:
        e.score = payload.Score
    else:
        cur_prob = prob or (
            {"sort_order": None}
            if e.probabilidad_item_id is None
            else _ensure_item_belongs_to(db, e.probabilidad_item_id, "probabilidad")
        )
        cur_imp = imp or (
            {"sort_order": None}
            if e.impacto_item_id is None
            else _ensure_item_belongs_to(db, e.impacto_item_id, "impacto")
        )
        e.score = _auto_score(cur_prob, cur_imp, None)

    db.merge(e)

    activos = [payload.ActivoID] if payload.ActivoID else None
    _sync_activos_rel(db, r.riesgo_id, activos)

    db.commit()
    db.refresh(r)
    return r


# ========== LISTADOS ENRIQUECIDOS (VISTAS con ORM) ==========
def list_generales_view(
    db: Session, user: dict, q: Optional[str], limit: int, offset: int
):
    ensure_authenticated(user)
    base = db.query(VRiesgoGeneralList).filter(
        VRiesgoGeneralList.empresa_id == user["empresa_id"]
    )
    if q:
        like = f"%{q}%"
        base = base.filter(
            or_(
                VRiesgoGeneralList.nombre.ilike(like),
                VRiesgoGeneralList.descripcion.ilike(like),
                VRiesgoGeneralList.responsable_nombre.ilike(like),
            )
        )
    total = base.with_entities(func.count()).scalar() or 0
    rows = (
        base.order_by(VRiesgoGeneralList.riesgo_id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    # Convertir ORM -> dict para respuesta uniforme
    return [r.__dict__ for r in rows], int(total)


def list_activos_view(
    db: Session, user: dict, q: Optional[str], limit: int, offset: int
):
    ensure_authenticated(user)
    base = db.query(VRiesgoActivoList).filter(
        VRiesgoActivoList.empresa_id == user["empresa_id"]
    )
    if q:
        like = f"%{q}%"
        base = base.filter(
            or_(
                VRiesgoActivoList.nombre.ilike(like),
                VRiesgoActivoList.descripcion.ilike(like),
                VRiesgoActivoList.propietario_nombre.ilike(like),
                VRiesgoActivoList.vulnerabilidad.ilike(like),
            )
        )
    total = base.with_entities(func.count()).scalar() or 0
    rows = (
        base.order_by(VRiesgoActivoList.riesgo_id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [r.__dict__ for r in rows], int(total)


# Mapa de IDs solicitados por ti
CATALOG_IDS = {
    "probabilidad": 11,
    "impacto": 12,
    "nivel_riesgo": 13,
    "amenaza": 14,
}


def _list_catalog_items_by_id(
    db: Session, empresa_id: int, catalog_id: int
) -> List[CatalogItem]:
    """
    Ítems de catálogo mezclando GLOBAL (empresa_id IS NULL) + específicos de la empresa,
    solo activos y no eliminados, ordenados por sort_order y name.
    """
    rows = (
        db.query(CatalogItem)
        .filter(CatalogItem.catalog_id == catalog_id)
        .filter(CatalogItem.active.is_(True))
        .filter(CatalogItem.deleted_at.is_(None))
        .filter(
           or_(CatalogItem.empresa_id.is_(None), CatalogItem.empresa_id == empresa_id)
        )
        .order_by(CatalogItem.sort_order, CatalogItem.name)
        .all()
    )
    return rows


def get_catalog_item(db, key: str, item_id: int):
    row = (
        db.execute(
            text("""
        SELECT ci.item_id, ci.code, ci.name, ci.sort_order
        FROM iso.catalog_item ci
        JOIN iso.catalog c ON c.catalog_id = ci.catalog_id
        WHERE c.catalog_key = :key AND ci.item_id = :item_id
    """),
            {"key": key, "item_id": item_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"El item_id {item_id} no pertenece al catálogo '{key}'.",
        )
    return row


def resolve_catalog_values(db, pairs: List[Dict[str, int]]):
    """
    pairs: [{"key":"probabilidad","item_id":45}, {"key":"impacto","item_id":50}, ...]
    Devuelve dict anidado { key: { item_id: item } }
    """
    if not pairs:
        return {}

    keys = list({p["key"] for p in pairs})
    ids = list({p["item_id"] for p in pairs})

    rows = (
        db.execute(
            text("""
        SELECT c.catalog_key AS key, ci.item_id, ci.code, ci.name, ci.sort_order
        FROM iso.catalog_item ci
        JOIN iso.catalog c ON c.catalog_id = ci.catalog_id
        WHERE c.catalog_key = ANY(:keys) AND ci.item_id = ANY(:ids)
    """),
            {"keys": keys, "ids": ids},
        )
        .mappings()
        .all()
    )

    out: Dict[str, Dict[int, Dict]] = {}
    for r in rows:
        out.setdefault(r["key"], {})[r["item_id"]] = {
            "item_id": r["item_id"],
            "code": r["code"],
            "name": r["name"],
            "sort_order": r["sort_order"],
        }
    return out
# Mapa de IDs solicitados por ti
CATALOG_IDS = {
    "probabilidad": 11,
    "impacto": 12,
    "nivel_riesgo": 13,
    "amenaza": 14,
}
def _list_catalog_items_by_id(
    db: Session, empresa_id: int, catalog_id: int
) -> List[CatalogItem]:
    """
    Ítems de catálogo mezclando GLOBAL (empresa_id IS NULL) + específicos de la empresa,
    solo activos y no eliminados, ordenados por sort_order y name.
    """
    rows = (
        db.query(CatalogItem)
        .filter(CatalogItem.catalog_id == catalog_id)
        .filter(CatalogItem.active.is_(True))
        .filter(CatalogItem.deleted_at.is_(None))
        .filter(
             or_(CatalogItem.empresa_id.is_(None), CatalogItem.empresa_id == empresa_id)
        )
        .order_by(CatalogItem.sort_order, CatalogItem.name)
        .all()
    )
    return rows
def list_probabilidad(db: Session, user: dict) -> List[CatalogItem]:
    ensure_authenticated(user)
    return _list_catalog_items_by_id(
        db, user["empresa_id"], CATALOG_IDS["probabilidad"]
    )


def list_impacto(db: Session, user: dict) -> List[CatalogItem]:
    ensure_authenticated(user)
    return _list_catalog_items_by_id(db, user["empresa_id"], CATALOG_IDS["impacto"])


def list_nivel_riesgo(db: Session, user: dict) -> List[CatalogItem]:
    ensure_authenticated(user)
    return _list_catalog_items_by_id(
        db, user["empresa_id"], CATALOG_IDS["nivel_riesgo"]
    )


def list_amenaza(db: Session, user: dict) -> List[CatalogItem]:
    ensure_authenticated(user)
    return _list_catalog_items_by_id(db, user["empresa_id"], CATALOG_IDS["amenaza"])
