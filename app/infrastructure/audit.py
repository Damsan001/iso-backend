from sqlalchemy import inspect, event
from sqlalchemy.orm import Session
from app.infrastructure.models import AuditLog
from app.infrastructure.audit_vars import current_actor  # <- usa la ContextVar compartida
from app.utils.decimal_utils import convert_decimal
from datetime import datetime

@event.listens_for(Session, "before_flush")
def audit_before_flush(session: Session, flush_context, instances):
    # Lee primero de session.info, luego de ContextVar
    actor = session.info.get("actor") or current_actor.get()

    def _pk_dict(obj):
        mapper = inspect(obj).mapper
        return {col.key: getattr(obj, col.key, None) for col in mapper.primary_key}

    def _pk_value(obj):
        mapper = inspect(obj).mapper
        pks = mapper.primary_key
        if len(pks) != 1:
            return None
        val = getattr(obj, pks[0].key, None)
        return val if isinstance(val, int) else None

    def _serialize_instance(obj):
        state = inspect(obj)
        return {attr.key: getattr(obj, attr.key) for attr in state.mapper.column_attrs}

    def _serialize_changes(obj):
        state = inspect(obj)
        before, after = {}, {}
        for attr in state.mapper.column_attrs:
            key = attr.key
            hist = state.attrs[key].history
            if not hist.has_changes():
                continue
            before[key] = hist.deleted[0] if hist.deleted else None
            after[key] = hist.added[0] if hist.added else getattr(obj, key)
        return before, after

    def serialize_for_json(data):
        if isinstance(data, dict):
            return {k: serialize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [serialize_for_json(i) for i in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    for obj in list(session.new):
        if isinstance(obj, AuditLog):
            continue
        session.add(AuditLog(
            table_name=inspect(obj).mapper.local_table.name,
            operation="CREATE",
            target_pk_id=_pk_value(obj),
            target_pk=serialize_for_json(convert_decimal(_pk_dict(obj))),
            actor=str(actor) if actor is not None else None,
            before=None,
            after=serialize_for_json(convert_decimal(_serialize_instance(obj))),
        ))

    for obj in list(session.dirty):
        if isinstance(obj, AuditLog):
            continue
        state = inspect(obj)
        if not state.modified:
            continue
        before, after = _serialize_changes(obj)
        if not before and not after:
            continue
        session.add(AuditLog(
            table_name=inspect(obj).mapper.local_table.name,
            operation="UPDATE",
            target_pk_id=_pk_value(obj),
            target_pk=serialize_for_json(convert_decimal(_pk_dict(obj))),
            actor=str(actor) if actor is not None else None,
            before=serialize_for_json(convert_decimal(before)),
            after=serialize_for_json(convert_decimal(after)),
        ))

    for obj in list(session.deleted):
        if isinstance(obj, AuditLog):
            continue
        state = inspect(obj)
        session.add(AuditLog(
            table_name=state.mapper.local_table.name,
            operation="DELETE",
            target_pk_id=_pk_value(obj),
            target_pk=serialize_for_json(_pk_dict(obj)),
            actor=str(actor) if actor is not None else None,
            before=serialize_for_json(_serialize_instance(obj)),
            after=None,
        ))