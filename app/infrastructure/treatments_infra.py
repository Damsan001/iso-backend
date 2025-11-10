from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, Text, TIMESTAMP, Integer, ForeignKey, String, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from app.infrastructure.models import Base  # Base con schema=iso

# ====== Entidad principal ======
# ====== Entidad principal ======
class Tratamiento(Base):
    __tablename__ = "tratamiento"
    tratamiento_id = Column(BigInteger, primary_key=True)
    empresa_id = Column(BigInteger, nullable=False)
    riesgo_id = Column(BigInteger, ForeignKey("riesgo.riesgo_id", ondelete="CASCADE"), nullable=False)

    # Plan de tratamiento (usar *_item_id)
    tipo_plan_item_id = Column(BigInteger, nullable=False)          # catalog_item_id
    responsable_id = Column(BigInteger, nullable=True)              # iso.usuario.usuario_id
    fecha_compromiso = Column(TIMESTAMP(timezone=True), nullable=True)
    estatus_item_id = Column(BigInteger, nullable=False)            # catalog_item_id
    justificacion_cambio_fecha = Column(Text, nullable=True)
    aprobador_cambio_fecha_id = Column(BigInteger, nullable=True)

    # Métricas (resumen)
    score_inicial = Column(Integer, nullable=True)
    efectividad_item_id = Column(BigInteger, nullable=True)         # catalog_item_id (1/2/3 en tu catálogo)
    residual_score = Column(Integer, nullable=True)
    residual_color_item_id = Column(BigInteger, nullable=True)      # opcional si lo tienes por catálogo

    # Auditoría
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


# ====== Controles asociados (N:M lógica) ======
class TratamientoControl(Base):
    __tablename__ = "tratamiento_control"
    tcontrol_id = Column(BigInteger, primary_key=True)
    tratamiento_id = Column(BigInteger, ForeignKey("tratamiento.tratamiento_id", ondelete="CASCADE"), nullable=False)

    # Catálogos/valores
    # Soportamos tanto ISO (p.ej. A.5.XX) como "CI.00X" internos
    tipo_control = Column(String, nullable=False)  # 'ISO' | 'CI'
    control_code = Column(String, nullable=False)  # 'A.5.1' | 'CI.001'
    control_name = Column(Text, nullable=False)    # nombre legible

    # Config específica
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)


# ====== Seguimientos (historial) ======
class TratamientoSeguimiento(Base):
    __tablename__ = "tratamiento_seguimiento"
    tseguimiento_id = Column(BigInteger, primary_key=True)
    tratamiento_id = Column(BigInteger, ForeignKey("tratamiento.tratamiento_id", ondelete="CASCADE"), nullable=False)
    responsable_id = Column(BigInteger, nullable=True)
    fecha = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    comentario = Column(Text, nullable=True)
    estatus = Column(String, nullable=True)  # opcional actualizar estatus desde el seguimiento


# ====== Evidencias ======
class TratamientoEvidencia(Base):
    __tablename__ = "tratamiento_evidencia"
    tevidencia_id = Column(BigInteger, primary_key=True)
    tratamiento_id = Column(BigInteger, ForeignKey("tratamiento.tratamiento_id", ondelete="CASCADE"), nullable=False)
    # Solo metadatos; el archivo puede gestionarse en /documents ya existente
    titulo = Column(Text, nullable=False)
    descripcion = Column(Text, nullable=True)
    url = Column(Text, nullable=True)  # o storage key
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)


# ====== Carta de aceptación ======
class CartaAceptacion(Base):
    __tablename__ = "tratamiento_carta_aceptacion"
    carta_id = Column(BigInteger, primary_key=True)
    tratamiento_id = Column(BigInteger, ForeignKey("tratamiento.tratamiento_id", ondelete="CASCADE"), nullable=False)
    requiere_dg = Column(Boolean, nullable=False, default=False)
    firmada_dg = Column(Boolean, nullable=False, default=False)
    firmada_propietario = Column(Boolean, nullable=False, default=False)
    justificacion = Column(Text, nullable=True)
    documento_url = Column(Text, nullable=True)  # si generas y guardas un PDF/Word
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)


# ====== Vista sencilla para listados (opcional, puedes crearla como view en DB) ======
class VTratamientoList(Base):
    __tablename__ = "v_tratamiento_list"
    __table_args__ = {"info": {"is_view": True}}
    tratamiento_id = Column(BigInteger, primary_key=True)
    empresa_id = Column(BigInteger)
    riesgo_id = Column(BigInteger)
    nombre_riesgo = Column(Text)      # join con riesgo.nombre
    tipo_plan = Column(String)
    responsable_id = Column(BigInteger)
    estatus = Column(String)
    score_inicial = Column(Integer)
    efectividad = Column(Integer)
    residual_score = Column(Integer)
    residual_color = Column(String)
    fecha_compromiso = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
