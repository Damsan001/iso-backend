from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.services.auth_service import ensure_authenticated, ensure_user_roles
from app.infrastructure.risks_infra import Riesgo, RiesgoGeneralExtra, RiesgoActivoExtra

# ------- Helpers -------
def _q_tratamiento_base(db: Session, empresa_id: int):
    from app.infrastructure.treatments_infra import Tratamiento
    return db.query(Tratamiento).filter(
        Tratamiento.empresa_id == empresa_id,
        Tratamiento.deleted_at.is_(None),
    )

def _calc_residual(score_inicial: Optional[int], efectividad: Optional[int]) -> tuple[Optional[int], Optional[str]]:
    if score_inicial is None or efectividad is None:
        return None, None
    residual = int(score_inicial) * int(efectividad)
    if residual <= 5:
        color = "verde"
    elif residual <= 11:
        color = "amarillo"
    else:
        color = "rojo"
    return residual, color

def _get_riesgo_score_inicial(db: Session, empresa_id: int, riesgo_id: int) -> int | None:
    r = db.query(Riesgo).filter(
        Riesgo.empresa_id == empresa_id,
        Riesgo.riesgo_id == riesgo_id,
        Riesgo.deleted_at.is_(None),
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Riesgo no encontrado")
    if r.tipo_riesgo == "general":
        e = db.query(RiesgoGeneralExtra).filter(RiesgoGeneralExtra.riesgo_id == riesgo_id).first()
        return e.score if e else None
    else:
        e = db.query(RiesgoActivoExtra).filter(RiesgoActivoExtra.riesgo_id == riesgo_id).first()
        return e.score if e else None

# ------- Catálogos -------
def get_catalog_items(db: Session, catalog_key: str) -> List[dict]:
    sql = text("""
        SELECT i.item_id, i.code, i.name, i.description, i.sort_order
        FROM iso.catalog c
        JOIN iso.catalog_item i ON i.catalog_id = c.catalog_id
        WHERE c.catalog_key = :ck AND COALESCE(i.active, true) = true
        ORDER BY i.sort_order NULLS LAST, i.name ASC
    """)
    rows = db.execute(sql, {"ck": catalog_key}).fetchall()
    return [
        dict(item_id=r.item_id, code=r.code, name=r.name, description=r.description, sort_order=r.sort_order)
        for r in rows
    ]

# ------- Buscador de riesgos -------
def search_risks_for_treatments(db: Session, user: dict, q: str, limit: int = 20) -> List[dict]:
    ensure_authenticated(user)
    empresa_id = int(user["empresa_id"])
    q = (q or "").strip().lower()
    qpat = f"%{q}%" if q else ""

    sql_general = text("""
        SELECT riesgo_id AS id, nombre AS name,probabilidad_nombre as prob,
        nivel_nombre as niv,impacto_nombre as imp,'' as amz,
        '' as vul,responsable_nombre as prop
        FROM iso.v_riesgo_general_list
        WHERE empresa_id = :eid
          AND (:q = '' OR LOWER(nombre) LIKE :qpat)
        ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST
        LIMIT :lim;
    """)
    sql_activo = text("""
        SELECT riesgo_id AS id, nombre AS name,probabilidad_nombre as prob,
        nivel_nombre as niv,impacto_nombre as imp,amenaza_nombre as amz,
        vulnerabilidad as vul, propietario_nombre as prop
        FROM iso.v_riesgo_activo_list
        WHERE empresa_id = :eid
          AND (:q = '' OR LOWER(nombre) LIKE :qpat)
        ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST
        LIMIT :lim;
    """)

    g = db.execute(sql_general, {"eid": empresa_id, "q": q, "qpat": qpat, "lim": limit}).fetchall()
    rem = max(0, limit - len(g))
    a = db.execute(sql_activo, {"eid": empresa_id, "q": q, "qpat": qpat, "lim": rem}).fetchall() if rem else []

    return [{"id": r.id, "name": r.name, "probabilidad_nombre": r.prob,"nivel_nombre": r.niv, "impacto_nombre":r.imp, "amenaza_nombre":r.amz,"vulnerabilidad":r.vul,"propietario_nombre":r.prop } for r in g] + [{"id": r.id, "name": r.name, "nivel_nombre": r.niv , "impacto_nombre":r.imp,"amenaza_nombre":r.amz,"vulnerabilidad":r.vul,"propietario_nombre":r.prop} for r in a]

# ------- CRUD Tratamientos -------
def list_tratamientos_paged(db: Session, user: dict, riesgo_id: Optional[int], q: Optional[str], limit: int, offset: int):
    from app.infrastructure.treatments_infra import Tratamiento
    ensure_authenticated(user)
    base = _q_tratamiento_base(db, user["empresa_id"])
    if riesgo_id:
        base = base.filter(Tratamiento.riesgo_id == riesgo_id)
    total = base.with_entities(func.count()).scalar() or 0
    items = base.order_by(Tratamiento.tratamiento_id.desc()).limit(limit).offset(offset).all()
    return items, total

def get_tratamiento(db: Session, user: dict, tratamiento_id: int):
    ensure_authenticated(user)
    return _q_tratamiento_base(db, user["empresa_id"]).filter_by(tratamiento_id=tratamiento_id).first()

def create_tratamiento(db: Session, user: dict, riesgo_id: int, payload):
    from app.infrastructure.treatments_infra import Tratamiento
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])

    score_inicial = _get_riesgo_score_inicial(db, user["empresa_id"], riesgo_id)
    residual_score, residual_color = _calc_residual(score_inicial, getattr(payload, "Efectividad", None))

    t = Tratamiento(
        empresa_id=user["empresa_id"],
        riesgo_id=riesgo_id,
        tipo_plan_item_id=getattr(payload, "TipoPlan", None) or getattr(payload, "TipoPlanID", None),
        responsable_id=getattr(payload, "ResponsableID", None),
        fecha_compromiso=datetime.fromisoformat(payload.FechaCompromiso) if getattr(payload, "FechaCompromiso", None) else None,
        estatus_item_id=getattr(payload, "Estatus", None) or getattr(payload, "EstatusID", None) or "en_proceso",
        score_inicial=score_inicial,
        efectividad_item_id=getattr(payload, "Efectividad", None) or getattr(payload, "EfectividadID", None),
        residual_score=residual_score,
        residual_color_item_id=residual_color,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def update_tratamiento(db: Session, user: dict, tratamiento_id: int, payload):
    from app.infrastructure.treatments_infra import Tratamiento
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])

    t = _q_tratamiento_base(db, user["empresa_id"]).filter_by(tratamiento_id=tratamiento_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")

    if getattr(payload, "TipoPlan", None) is not None: t.tipo_plan = payload.TipoPlan
    if getattr(payload, "TipoPlanID", None) is not None: t.tipo_plan = payload.TipoPlanID
    if getattr(payload, "ResponsableID", None) is not None: t.responsable_id = payload.ResponsableID
    if hasattr(payload, "FechaCompromiso"):
        t.fecha_compromiso = datetime.fromisoformat(payload.FechaCompromiso) if payload.FechaCompromiso else None
    if getattr(payload, "Efectividad", None) is not None: t.efectividad = payload.Efectividad
    if getattr(payload, "EfectividadID", None) is not None: t.efectividad = payload.EfectividadID
    if getattr(payload, "Estatus", None) is not None: t.estatus = payload.Estatus
    if getattr(payload, "EstatusID", None) is not None: t.estatus = payload.EstatusID
    if getattr(payload, "JustificacionCambioFecha", None) is not None: t.justificacion_cambio_fecha = payload.JustificacionCambioFecha
    if getattr(payload, "AprobadorCambioFechaID", None) is not None: t.aprobador_cambio_fecha_id = payload.AprobadorCambioFechaID

    t.residual_score, t.residual_color = _calc_residual(t.score_inicial, t.efectividad)

    db.commit()
    db.refresh(t)
    return t

def delete_tratamiento(db: Session, user: dict, tratamiento_id: int):
    from app.infrastructure.treatments_infra import Tratamiento
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])
    t = _q_tratamiento_base(db, user["empresa_id"]).filter_by(tratamiento_id=tratamiento_id).first()
    if not t: return
    t.deleted_at = datetime.now(tz=timezone.utc)
    db.commit()

# ------- Controles -------
def add_control(db: Session, user: dict, tratamiento_id: int, payload):
    from app.infrastructure.treatments_infra import TratamientoControl
    ensure_authenticated(user)
    ensure_user_roles(user, ["Administrador", "Supervisor"])
    row = TratamientoControl(
        tratamiento_id=tratamiento_id,
        tipo_control=payload.TipoControl,
        control_code=(payload.ControlCode or "").strip() or None,
        control_name=(payload.ControlName or "").strip(),
        observaciones=getattr(payload, "Observaciones", None),
        activo=True if getattr(payload, "Activo", True) else False,
    )
    if row.tipo_control == "CI" and not row.control_code:
        last = db.query(TratamientoControl).order_by(TratamientoControl.tcontrol_id.desc()).first()
        next_num = (last.tcontrol_id + 1) if last else 1
        row.control_code = f"CI.{next_num:03d}"
    db.add(row); db.commit(); db.refresh(row); return row

def remove_control(db: Session, user: dict, tratamiento_id: int, tcontrol_id: int):
    from app.infrastructure.treatments_infra import TratamientoControl
    ensure_authenticated(user); ensure_user_roles(user, ["Administrador", "Supervisor"])
    row = db.query(TratamientoControl).filter_by(tratamiento_id=tratamiento_id, tcontrol_id=tcontrol_id).first()
    if not row: return
    db.delete(row); db.commit()

# ------- Seguimientos -------
def add_seguimiento(db: Session, user: dict, tratamiento_id: int, payload):
    from app.infrastructure.treatments_infra import TratamientoSeguimiento
    ensure_authenticated(user)
    fecha = datetime.fromisoformat(payload.Fecha) if getattr(payload, "Fecha", None) else datetime.now(tz=timezone.utc)
    row = TratamientoSeguimiento(
        tratamiento_id=tratamiento_id,
        responsable_id=getattr(payload, "ResponsableID", None),
        fecha=fecha,
        comentario=getattr(payload, "Comentario", None),
        estatus=getattr(payload, "Estatus", None),
    )
    db.add(row); db.commit(); db.refresh(row); return row

def list_seguimientos(db: Session, user: dict, tratamiento_id: int):
    from app.infrastructure.treatments_infra import TratamientoSeguimiento
    ensure_authenticated(user)
    return (
        db.query(TratamientoSeguimiento)
        .filter_by(tratamiento_id=tratamiento_id)
        .order_by(TratamientoSeguimiento.tseguimiento_id.desc())
        .all()
    )

# ------- Evidencias -------
def add_evidencia(db: Session, user: dict, tratamiento_id: int, payload):
    from app.infrastructure.treatments_infra import TratamientoEvidencia
    ensure_authenticated(user)
    row = TratamientoEvidencia(
        tratamiento_id=tratamiento_id,
        titulo=(payload.Titulo or "").strip(),
        descripcion=getattr(payload, "Descripcion", None),
        url=getattr(payload, "Url", None),
    )
    db.add(row); db.commit(); db.refresh(row); return row

# ------- Carta de aceptación -------
def generar_carta_aceptacion(db: Session, user: dict, tratamiento_id: int, justificacion: str | None):
    from app.infrastructure.treatments_infra import CartaAceptacion
    ensure_authenticated(user)
    t = get_tratamiento(db, user, tratamiento_id)
    if not t: raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    if t.residual_score is None: raise HTTPException(status_code=400, detail="No es posible determinar el residual.")
    requiere_dg = t.residual_score > 5
    carta = CartaAceptacion(
        tratamiento_id=tratamiento_id,
        requiere_dg=requiere_dg,
        firmada_dg=False,
        firmada_propietario=False,
        justificacion=justificacion,
        documento_url=None,
    )
    db.add(carta); db.commit(); db.refresh(carta); return carta
