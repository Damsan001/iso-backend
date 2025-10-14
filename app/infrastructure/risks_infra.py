from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, Text, TIMESTAMP, Integer, ForeignKey, String, Integer as Int
)
from sqlalchemy.dialects.postgresql import JSONB
from app.infrastructure.models import Base  # Base con schema=iso
from sqlalchemy.sql.schema import FetchedValue

# ========= Tablas base =========
class Riesgo(Base):
    __tablename__ = "riesgo"
    riesgo_id   = Column(BigInteger, primary_key=True)
    empresa_id  = Column(BigInteger, nullable=False)
    tipo_riesgo = Column(Text, nullable=False)   # 'general' | 'activo'
    nombre      = Column(Text, nullable=False)
    descripcion = Column(Text)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at  = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at  = Column(TIMESTAMP(timezone=True), nullable=True)

class RiesgoGeneralExtra(Base):
    __tablename__ = "riesgo_general"
    riesgo_id            = Column(BigInteger, ForeignKey("riesgo.riesgo_id", ondelete="CASCADE"), primary_key=True)
    responsable_id       = Column(BigInteger, nullable=True)   # -> iso.usuario.usuario_id
    probabilidad_item_id = Column(BigInteger, nullable=True)   # -> iso.catalog_item.item_id
    impacto_item_id      = Column(BigInteger, nullable=True)
    nivel_item_id        = Column(BigInteger, nullable=True)
    score                = Column(Integer,   nullable=True)

class RiesgoActivoExtra(Base):
    __tablename__ = "riesgo_activo"
    riesgo_id            = Column(BigInteger, ForeignKey("riesgo.riesgo_id", ondelete="CASCADE"), primary_key=True)
    activo_id            = Column(BigInteger, nullable=True)   # (legacy) un activo
    amenaza_item_id      = Column(BigInteger, nullable=True)
    vulnerabilidad       = Column(Text,      nullable=True)
    propietario_id       = Column(BigInteger, nullable=True)
    probabilidad_item_id = Column(BigInteger, nullable=True)
    impacto_item_id      = Column(BigInteger, nullable=True)
    nivel_item_id        = Column(BigInteger, nullable=True)
    score                = Column(Integer,   nullable=True)
    integridad_item_id   = Column(BigInteger, nullable=True)
    disponibilidad_item_id   = Column(BigInteger, nullable=True)
    confidencialidad_item_id   = Column(BigInteger, nullable=True)
    

class RiesgoActivoRel(Base):
    __tablename__ = "riesgo_activo_rel"
    riesgo_id = Column(BigInteger, ForeignKey("riesgo.riesgo_id", ondelete="CASCADE"), primary_key=True)
    activo_id = Column(BigInteger, primary_key=True)

# ========= Catálogos (para validar por ORM) =========
class Catalog(Base):
    __tablename__ = "catalog"
    catalog_id = Column(BigInteger, primary_key=True)
    catalog_key = Column(String, nullable=False)

class CatalogItem(Base):
    __tablename__ = "catalog_item"
    item_id   = Column(BigInteger, primary_key=True)
    catalog_id = Column(BigInteger, ForeignKey("catalog.catalog_id"), nullable=False)
    code       = Column(String)
    name       = Column(String)
    sort_order = Column(Int)

# ========= VISTAS mapeadas (solo lectura) =========
class VRiesgoGeneralList(Base):
    __tablename__ = "v_riesgo_general_list"
    __table_args__ = {"info": {"is_view": True}}
    # Primary key lógico para permitir orden/paginación ORM
    riesgo_id          = Column(BigInteger, primary_key=True)
    empresa_id         = Column(BigInteger)
    nombre             = Column(Text)
    descripcion        = Column(Text)
    created_at         = Column(TIMESTAMP(timezone=True))
    updated_at         = Column(TIMESTAMP(timezone=True))
    responsable_id     = Column(BigInteger)
    responsable_nombre = Column(Text)
    probabilidad_item_id = Column(BigInteger)
    probabilidad_nombre  = Column(Text)
    probabilidad_orden   = Column(Int)
    impacto_item_id      = Column(BigInteger)
    impacto_nombre       = Column(Text)
    impacto_orden        = Column(Int)
    nivel_item_id        = Column(BigInteger)
    nivel_nombre         = Column(Text)
    nivel_orden          = Column(Int)
    score                = Column(Int)
        
class VRiesgoActivoList(Base):
    __tablename__ = "v_riesgo_activo_list"
    __table_args__ = {"info": {"is_view": True}}
    riesgo_id          = Column(BigInteger, primary_key=True)
    empresa_id         = Column(BigInteger)
    nombre             = Column(Text)
    descripcion        = Column(Text)
    created_at         = Column(TIMESTAMP(timezone=True))
    updated_at         = Column(TIMESTAMP(timezone=True))
    vulnerabilidad     = Column(Text)
    propietario_id     = Column(BigInteger)
    propietario_nombre = Column(Text)
    amenaza_item_id    = Column(BigInteger)
    amenaza_nombre     = Column(Text)
    probabilidad_item_id = Column(BigInteger)
    probabilidad_nombre  = Column(Text)
    probabilidad_orden   = Column(Int)
    impacto_item_id      = Column(BigInteger)
    impacto_nombre       = Column(Text)
    impacto_orden        = Column(Int)
    nivel_item_id        = Column(BigInteger)
    nivel_nombre         = Column(Text)
    nivel_orden          = Column(Int)
    score                = Column(Int)
    activos             = Column(JSONB)  # jsonb_agg
    intgiridad_item_id      = Column(BigInteger)
    integridad_nombre       = Column(Text)
    integridad_orden        = Column(Int)
    disponibilidad_item_id  = Column(BigInteger)
    disponibilidad_nombre   = Column(Text)
    disponibilidad_orden    = Column(Int)
    confidencialidad_item_id = Column(BigInteger)
    confidencialidad_nombre  = Column(Text)
    confidencialidad_orden   = Column(Int)
