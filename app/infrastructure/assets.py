# Archivo Infraestructura/ Assets
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    MetaData,
    Numeric,
    Text,
    TIMESTAMP,
    create_engine,
    or_,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

# ===========================
# Conexión y Base
# ===========================
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Ajusta el fallback a lo que uses localmente
    "postgresql+psycopg2://admin:admin123@localhost:5432/postgres",
)

# Forzamos el schema por defecto a iso (también calificamos con metadata.schema)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"options": "-csearch_path=iso"},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

metadata = MetaData(schema="iso")
Base = declarative_base(metadata=metadata)


# ===========================
# Modelos de Catálogos
# ===========================
class Catalog(Base):
    __tablename__ = "catalog"
    catalog_id = Column(BigInteger, primary_key=True)
    catalog_key = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    is_hierarchical = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)


class CatalogItem(Base):
    __tablename__ = "catalog_item"
    item_id = Column(BigInteger, primary_key=True)
    catalog_id = Column(
        BigInteger, ForeignKey("iso.catalog.catalog_id"), nullable=False
    )
    empresa_id = Column(BigInteger, nullable=True)  # NULL = global
    code = Column(Text)
    name = Column(Text, nullable=False)
    description = Column(Text)
    sort_order = Column(BigInteger, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    parent_item_id = Column(
        BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    catalog = relationship("Catalog", lazy="selectin")


# ===========================
# Modelo Activo
# ===========================
class Activo(Base):
    __tablename__ = "activo"

    activo_id = Column(BigInteger, primary_key=True)
    empresa_id = Column(BigInteger, nullable=False)

    nombre = Column(Text, nullable=False)

    # Catálogos
    tipo_item_id = Column(
        BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True
    )
    estado_item_id = Column(
        BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True
    )
    clasificacion_item_id = Column(
        BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True
    )
    area_item_id = Column(
        BigInteger, ForeignKey("iso.catalog_item.item_id"), nullable=True
    )  # NUEVO

    # Datos libres
    descripcion = Column(Text, nullable=True)
    ubicacion = Column(Text, nullable=True)
    fecha_adquisicion = Column(Date, nullable=True)
    valor = Column(Numeric(14, 2), nullable=True)
    numero_serie = Column(Text, nullable=True)
    modelo = Column(Text, nullable=True)
    marca = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relaciones (cargadas al vuelo para facilitar serialización)
    tipo = relationship("CatalogItem", foreign_keys=[tipo_item_id], lazy="joined")
    estado = relationship("CatalogItem", foreign_keys=[estado_item_id], lazy="joined")
    clasificacion = relationship(
        "CatalogItem", foreign_keys=[clasificacion_item_id], lazy="joined"
    )
    area = relationship(
        "CatalogItem", foreign_keys=[area_item_id], lazy="joined"
    )  # NUEVA


# ===========================
# Helpers
# ===========================
def get_catalog_items(db: Session, catalog_key: str, empresa_id: int):
    """
    Devuelve ítems de un catálogo combinando GLOBAL (empresa_id IS NULL)
    + específicos de la empresa.
    """
    q = (
        db.query(CatalogItem)
        .join(Catalog, Catalog.catalog_id == CatalogItem.catalog_id)
        .filter(Catalog.catalog_key == catalog_key)
        .filter(CatalogItem.active.is_(True))
        .filter(CatalogItem.deleted_at.is_(None))
        .filter(
            or_(CatalogItem.empresa_id.is_(None), CatalogItem.empresa_id == empresa_id)
        )
        .order_by(CatalogItem.sort_order, CatalogItem.name)
    )
    return q.all()
