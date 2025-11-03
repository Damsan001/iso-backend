from fastapi import UploadFile, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session,aliased
from starlette import status
from datetime import datetime
from app.infrastructure.models import Documento, CatalogItem, DocumentoVersion, Areas
from app.schemas.Dtos.DocumentDtos import DocumentCreateDto, DocumentVesionDto
from app.services.auth_service import check_auth_and_roles
from app.services.google_cloud_aservice import upload_file_to_gcs, generate_signed_url
from app.utils.documents_utils import generar_codigo_documento
from urllib.parse import urlparse

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
    file_url = upload_file_to_gcs(file, f"{code_document}-v1.pdf")
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
        archivo_url= file_url
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
            DocumentoVersion.version_id,
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

def view_document_service(db: Session, version_id: int) -> str:
    """
    Devuelve una URL firmada para visualizar el documento.
    """
    document_version = (
        db.query(DocumentoVersion.archivo_url)
        .join(Documento, Documento.documento_id == DocumentoVersion.documento_id)
        .filter(DocumentoVersion.version_id == version_id)
        .first()
    )
    if not document_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado."
        )
    parsed_url = urlparse(document_version.archivo_url)
    blob_name = parsed_url.path.split('/')[-1]
    return generate_signed_url(blob_name)


def create_document_version_service(db: Session, user: dict, document_code: str, document_data: DocumentVesionDto,
                                    file: UploadFile):
    check_auth_and_roles(user, ["admin", "Administrador"])

    # Verificar que el documento existe por código
    existing_document = db.query(Documento).filter(Documento.codigo == document_code).first()
    if not existing_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado."
        )

    # Obtener estados "En revisión" y "Por Autorizar"
    revision_state = db.query(CatalogItem).filter(CatalogItem.name == "En revisión").first()
    authorization_state = db.query(CatalogItem).filter(CatalogItem.name == "Por Autorizar").first()

    # Validar si hay una versión en revisión o por autorizar
    if revision_state or authorization_state:
        states_to_check = [s.item_id for s in [revision_state, authorization_state] if s]
        existing_pending = db.query(DocumentoVersion).filter(
            DocumentoVersion.documento_id == existing_document.documento_id,
            DocumentoVersion.estado_item_id.in_(states_to_check)
        ).first()
        if existing_pending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una versión en revisión o por autorizar. No se puede crear una nueva versión."
            )

    # Obtener la última versión usando documento_id
    last_version = (
        db.query(func.max(DocumentoVersion.numero_version))
        .filter(DocumentoVersion.documento_id == existing_document.documento_id)
        .scalar()
    )
    new_version_number = (last_version or 0) + 1

    # Generar nombre del archivo con versión
    file_name = f"{existing_document.codigo}-v{new_version_number}.pdf"
    file_url = upload_file_to_gcs(file, file_name)

    # Obtener estado inicial (similar a create_documents_service)
    initial_state = db.query(CatalogItem).filter(CatalogItem.name == "En revisión").first()

    # Crear nueva versión
    new_version = DocumentoVersion(
        documento_id=existing_document.documento_id,
        numero_version=new_version_number,
        creado_por_id=document_data.creador_id,
        estado_item_id=initial_state.item_id,
        creado_en=datetime.now(),
        revisado_por_id=document_data.revisado_por_id,
        aprobado_por_id=document_data.aprobador_por_id,
        archivo_url=file_url
    )
    db.add(new_version)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear la versión por conflicto de integridad.",
        ) from e

    return f"Versión {new_version_number} del documento creada correctamente"

