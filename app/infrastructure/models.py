from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, ForeignKey,
    Numeric, Text,DateTime,Integer,Index, text, String, JSON, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, SCHEMA_NAME

# Tabla intermedia para la relación muchos a muchos entre Usuario y Rol
usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", BigInteger, ForeignKey(f"{SCHEMA_NAME}.rol.rol_id", ondelete="CASCADE"), primary_key=True),
    schema=SCHEMA_NAME
)

# --- Generic catalogs (iso.catalog & iso.catalog_item) ---
class Catalog(Base):
    __tablename__ = "catalog"
    __table_args__ = {"schema": SCHEMA_NAME}
    catalog_id = Column(BigInteger, primary_key=True, autoincrement=True)
    catalog_key = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    is_hierarchical = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class CatalogItem(Base):
    __tablename__ = "catalog_item"
    __table_args__ = {"schema": SCHEMA_NAME}
    item_id = Column(BigInteger, primary_key=True, autoincrement=True)
    catalog_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog.catalog_id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id"), nullable=True)
    code = Column(Text)
    name = Column(Text, nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    active = Column(Boolean, nullable=False, default=True, server_default="true")
    parent_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))

# --- Assets (iso.activo) ---
class Activo(Base):
    __tablename__ = "activo"
    __table_args__ = {"schema": SCHEMA_NAME}

    activo_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id"), nullable=False)
    nombre = Column(Text, nullable=False)
    tipo_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    estado_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    clasificacion_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    propietario_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=True)
    custodio_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=True)
    descripcion = Column(Text)
    ubicacion = Column(Text)
    fecha_adquisicion = Column(Date)
    valor = Column(Numeric(18, 2))
    numero_serie = Column(Text)
    marca = Column(Text)
    modelo = Column(Text)
    imagen_url = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    area_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)

class ComentarioRevision(Base):
    __tablename__ = "comentario_revision"
    __table_args__ = {"schema": SCHEMA_NAME}
    comentario_id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.documento_version.version_id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=False)
    comentario = Column(Text, nullable=False)
    archivo_url = Column(Text)
    fecha = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    estatus_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True))

class Documento(Base):
    __tablename__ = "documento"
    __table_args__ = {"schema": SCHEMA_NAME}
    documento_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id"), nullable=False)
    nombre = Column(Text, nullable=False)
    codigo = Column(Text)
    tipo_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    area_responsable_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    clasificacion_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    visible_empresa = Column(Boolean, nullable=False, default=True, server_default="true")
    creador_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
class DocumentoACL(Base):
    __tablename__ = "documento_acl"
    __table_args__ = {"schema": SCHEMA_NAME}
    acl_id = Column(BigInteger, primary_key=True, autoincrement=True)
    documento_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.documento.documento_id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id"), nullable=True)
    rol_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    area_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=True)
    permiso_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    nivel = Column(Integer, nullable=False, default=0, server_default="0")
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))

class DocumentoVersion(Base):
    __tablename__ = "documento_version"
    __table_args__ = {"schema": SCHEMA_NAME}
    version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    documento_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.documento.documento_id", ondelete="CASCADE"), nullable=False)
    numero_version = Column(Integer, nullable=False)
    descripcion = Column(Text)
    justificacion = Column(Text)
    estado_item_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.catalog_item.item_id"), nullable=False)
    archivo_url = Column(Text)
    creado_por_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    aprobado_por_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id"), nullable=True)
    fecha_autorizacion = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

class Empresa(Base):
    __tablename__ = "empresa"
    __table_args__ = {"schema": SCHEMA_NAME}
    empresa_id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre_legal = Column(Text, nullable=False)
    rfc = Column(Text)
    estatus = Column(Text)
    fecha_registro = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))

class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        Index("uq_usuario_empresa_email", "empresa_id", text("lower(email)"), unique=True),
        {"schema": SCHEMA_NAME},
    )
    usuario_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id", ondelete="CASCADE"), nullable=False)
    area_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.areas.area_id", ondelete="RESTRICT"), nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    hashed_password = Column(String)
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    area = relationship("Areas", back_populates="usuarios")
    roles = relationship("Rol", secondary=f"{SCHEMA_NAME}.usuario_rol", back_populates="usuarios")
    permisos_directos = relationship(
        "Permiso",
        secondary=f"{SCHEMA_NAME}.usuario_permiso",
        back_populates="usuarios_directos"
    )

class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = (
        Index("uq_rol_empresa_nombre", "empresa_id", text("lower(nombre)"), unique=True),
        {"schema": SCHEMA_NAME},
    )
    rol_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id", ondelete="CASCADE"), nullable=False)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    usuarios = relationship("Usuario", secondary=f"{SCHEMA_NAME}.usuario_rol", back_populates="roles")
    permisos = relationship("Permiso", secondary=f"{SCHEMA_NAME}.rol_permiso", backref="roles")

class Permiso(Base):
    __tablename__ = "permiso"
    __table_args__ = (
        Index("uq_permiso_scope", "empresa_id", text("upper(codigo)"), unique=True),
        {"schema": SCHEMA_NAME},
    )
    permiso_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id", ondelete="CASCADE"), nullable=True)
    codigo = Column(Text, nullable=False)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    usuarios_directos = relationship(
        "Usuario",
        secondary=f"{SCHEMA_NAME}.usuario_permiso",
        back_populates="permisos_directos"
    )

class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    __table_args__ = {"schema": SCHEMA_NAME}
    rol_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.rol.rol_id", ondelete="CASCADE"), primary_key=True)
    permiso_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.permiso.permiso_id", ondelete="CASCADE"), primary_key=True)

class UsuarioPermiso(Base):
    __tablename__ = "usuario_permiso"
    __table_args__ = {"schema": SCHEMA_NAME}
    usuario_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.usuario.usuario_id", ondelete="CASCADE"), primary_key=True)
    permiso_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.permiso.permiso_id", ondelete="CASCADE"), primary_key=True)
    concedido = Column(Boolean, nullable=False)

class Areas(Base):
    __tablename__ = "areas"
    __table_args__ = (
        Index("uq_areas_empresa_nombre", "empresa_id", text("lower(nombre)"), unique=True),
        {"schema": SCHEMA_NAME},
    )

    area_id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey(f"{SCHEMA_NAME}.empresa.empresa_id", ondelete="CASCADE"), nullable=False)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
    usuarios = relationship("Usuario", back_populates="area")

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    table_name = Column(String(128), nullable=False)
    operation = Column(String(16), nullable=False)
    target_pk_id = Column(Integer, nullable=True, index=True)
    target_pk = Column(JSON, nullable=False)
    actor = Column(String(128), nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
