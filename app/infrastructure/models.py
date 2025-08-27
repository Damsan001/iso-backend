from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, ForeignKey,
    Numeric, Text, TIMESTAMP
)
from sqlalchemy.orm import relationship
from .db import Base

# --- Generic catalogs (iso.catalog & iso.catalog_item) ---
class Catalog(Base):
    __tablename__ = "catalog"
    catalog_id = Column(BigInteger, primary_key=True)
    catalog_key = Column(Text, nullable=False, unique=True)  # e.g. "tipo_activo"
    name = Column(Text, nullable=False)
    description = Column(Text)
    is_hierarchical = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

class CatalogItem(Base):
    __tablename__ = "catalog_item"
    item_id = Column(BigInteger, primary_key=True)
    catalog_id = Column(BigInteger, ForeignKey("iso.catalog.catalog_id"), nullable=False)
    empresa_id = Column(BigInteger, nullable=True)  # NULL means global
    code = Column(Text)
    name = Column(Text, nullable=False)
    description = Column(Text)
    sort_order = Column(BigInteger, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    parent_item_id = Column(BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    catalog = relationship("Catalog", lazy="selectin")

# --- Assets (iso.activo) ---
class Activo(Base):
    __tablename__ = "activo"

    activo_id = Column(BigInteger, primary_key=True)
    empresa_id = Column(BigInteger, nullable=False)

    nombre = Column(Text, nullable=False)
    marca = Column(Text, nullable=False)
    # Catalog references
    tipo_item_id = Column(BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True)
    estado_item_id = Column(BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True)
    clasificacion_item_id = Column(BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True)
    area_item_id = Column(BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True)

    # Free fields
    descripcion = Column(Text)
    ubicacion = Column(Text)
    fecha_adquisicion = Column(Date)
    valor = Column(Numeric(14, 2))
    numero_serie = Column(Text)
    modelo = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Joined relationships to expose readable names in responses if desired
    tipo = relationship("CatalogItem", foreign_keys=[tipo_item_id], lazy="joined")
    estado = relationship("CatalogItem", foreign_keys=[estado_item_id], lazy="joined")
    clasificacion = relationship("CatalogItem", foreign_keys=[clasificacion_item_id], lazy="joined")
    area = relationship("CatalogItem", foreign_keys=[area_item_id], lazy="joined")
