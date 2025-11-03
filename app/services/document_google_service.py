from fastapi import UploadFile, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session,aliased
from starlette import status
from datetime import datetime
from app.infrastructure.models import Documento, CatalogItem, DocumentoVersion, Areas
from app.schemas.Dtos.DocumentDtos import DocumentCreateDto
from app.services.auth_service import check_auth_and_roles
from app.utils.documents_utils import generar_codigo_documento


def serialize_for_json(data):
    from datetime import datetime
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_for_json(i) for i in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def create_documents_service(db: Session, user: dict, document_data: DocumentCreateDto, file : UploadFile):
    check_auth_and_roles(user, ["admin", "Administrador"])

    existing_document = (db.query(Documento)
                         .filter(Documento.nombre == document_data.nombre)
                         .filter(Documento.tipo_item_id == document_data.tipo_item_id)
                         .first())
    if existing_document:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El documento ya existe. Para nuevas versiones, use el endpoint de versionado."
        )

    code_document_type = (db.query(CatalogItem)
                          .filter(CatalogItem.item_id == document_data.tipo_item_id)
                          .first()
                          )

    initial_state = (db.query(CatalogItem)
                     .filter(CatalogItem.name == "En revisión")
                     .first()
                     )


    if not code_document_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de documento no válido."
        )

    valor : str = code_document_type.code
    code_document = generar_codigo_documento(db, valor)
    # Crear nuevo documento
    new_document = Documento(
        nombre=document_data.nombre,
        codigo=code_document,
        empresa_id=user.get('empresa_id'),
        tipo_item_id=document_data.tipo_item_id,
        area_responsable_item_id=document_data.area_responsable_item_id,
        creador_id=document_data.creador_id,
        clasificacion_item_id=document_data.clasificacion_item_id
    )

    db.add(new_document)
    db.flush()

    new_version = DocumentoVersion(
        documento_id=new_document.documento_id,
        numero_version=1,  # Primera versión
        creado_por_id=document_data.creador_id,
        estado_item_id=initial_state.item_id,
        creado_en=datetime.now(),
        revisado_por_id=document_data.revisado_por_id,
        aprobado_por_id=document_data.aprobador_por_id,
        archivo_url=f"/storage/{code_document}-v1.pdf"
    )
    db.add(new_version)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear el documento por conflicto de integridad.",
        ) from e

    return "Documento creado correctamente"

def get_documents_service(db: Session):
    tipo_item = aliased(CatalogItem)
    clasificacion_item = aliased(CatalogItem)
    estado_item = aliased(CatalogItem)

    resultados = (
        db.query(
            Documento.codigo,
            Documento.nombre,
            DocumentoVersion.numero_version,
            tipo_item.name.label("tipo"),
            Areas.nombre.label("area"),
            estado_item.name.label("estado"),
            clasificacion_item.name.label("clasificacion"),
            func.to_char(Documento.created_at, 'DD-MM-YY').label("creado"),
            DocumentoVersion.archivo_url.label("url")
        )
        .join(DocumentoVersion, DocumentoVersion.documento_id == Documento.documento_id)
        .join(tipo_item, tipo_item.item_id == Documento.tipo_item_id)
        .join(Areas, Areas.area_id == Documento.area_responsable_item_id)
        .join(clasificacion_item, clasificacion_item.item_id == Documento.clasificacion_item_id)
        .join(estado_item, estado_item.item_id == DocumentoVersion.estado_item_id)
        .all()
    )
    return [dict(r._mapping) for r in resultados]


def get_document_by_id_service(db: Session, document_id: int):
    tipo_item = aliased(CatalogItem)
    clasificacion_item = aliased(CatalogItem)
    estado_item = aliased(CatalogItem)

    resultado = (
        db.query(
            Documento.codigo,
            Documento.nombre,
            DocumentoVersion.numero_version,
            tipo_item.name.label("tipo"),
            Areas.nombre.label("area"),
            estado_item.name.label("estado"),
            clasificacion_item.name.label("clasificacion"),
            func.to_char(Documento.created_at, 'DD-MM-YY').label("creado"),
            DocumentoVersion.archivo_url.label("url")
        )
        .join(DocumentoVersion, DocumentoVersion.documento_id == Documento.documento_id)
        .join(tipo_item, tipo_item.item_id == Documento.tipo_item_id)
        .join(Areas, Areas.area_id == Documento.area_responsable_item_id)
        .join(clasificacion_item, clasificacion_item.item_id == Documento.clasificacion_item_id)
        .join(estado_item, estado_item.item_id == DocumentoVersion.estado_item_id)
        .filter(Documento.documento_id == document_id)
        .first()
    )
    return dict(resultado._mapping) if resultado else None