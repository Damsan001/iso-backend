import re

from fastapi import UploadFile, HTTPException
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from starlette import status
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
import os
from google.cloud import storage
from PIL import Image as PILImage
import io

from app.infrastructure.models import Documento, CatalogItem, DocumentoVersion, Areas, Usuario, ComentarioRevision, \
    Empresa
from app.schemas.Dtos.DocumentDtos import DocumentCreateDto, DocumentVersionDto, ComentarioRevisionDto, \
    NotificationEmailDto
from app.services.auth_service import check_auth_and_roles
from app.services.google_cloud_aservice import upload_file_to_gcs, generate_signed_url
from app.utils.documents_utils import generar_codigo_documento
from urllib.parse import urlparse

from app.utils.send_email import send_email_notification


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



def create_documents_service(db: Session, user: dict, document_data: DocumentCreateDto, file: UploadFile):
    check_auth_and_roles(user, ["admin", "Administrador"])

    if (document_data.creador_id == document_data.revisado_por_id or
            document_data.creador_id == document_data.aprobado_por_id or
            document_data.revisado_por_id == document_data.aprobado_por_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los IDs de creador, revisor y aprobador deben ser diferentes."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF."
        )

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

    valor: str = code_document_type.code
    code_document = generar_codigo_documento(db, valor)
    file_url = upload_file_to_gcs(file, f"{code_document}-v1.pdf")
    # file_url = f"{code_document}-v1.pdf"
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
        aprobado_por_id=document_data.aprobado_por_id,
        archivo_url=file_url
    )
    db.add(new_version)

    try:
        db.commit()
        send_document_notifications(db=db, version_id=new_version.version_id)
        _overlay_pdf_with_status_image(
            db,
            new_version.archivo_url,
            initial_state.item_id,
            signer_name=str(document_data.creador_id),
            fecha=datetime.now( )
        )

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear el documento por conflicto de integridad.",
        ) from e

    return "Documento creado correctamente"


def get_documents_service(db: Session, user: dict):
    rol = user.get('rol')
    usuario_id = user.get('usuario_id')
    area_id = user.get('area_id')
    empresa_id = user.get('empresa_id')

    # Obtener item_id de estados
    aprobado_state = db.query(CatalogItem).filter(CatalogItem.name == "Aprobado").first()
    aprobado_id = aprobado_state.item_id if aprobado_state else None

    tipo_item = aliased(CatalogItem)
    clasificacion_item = aliased(CatalogItem)
    estado_item = aliased(CatalogItem)

    query = (
        db.query(
            Documento.codigo,
            Documento.nombre,
            Documento.documento_id,
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
        .filter(Documento.empresa_id == empresa_id)  # Filtro por empresa para seguridad
    )

    if rol == "Usuario Estándar":
        query = query.filter(
            (Documento.area_responsable_item_id == area_id) |
            (DocumentoVersion.estado_item_id == aprobado_id) |
            (DocumentoVersion.revisado_por_id == usuario_id) |
            (DocumentoVersion.aprobado_por_id == usuario_id)
        )
    elif rol == "Alta Dirección":
        if aprobado_id:
            query = query.filter(DocumentoVersion.estado_item_id == aprobado_id)

    # Para Administrador, no se aplica filtro adicional

    resultados = query.all()
    return [dict(r._mapping) for r in resultados]


def get_document_by_id_service(db: Session, document_id: int):
    tipo_item = aliased(CatalogItem)
    clasificacion_item = aliased(CatalogItem)
    estado_item = aliased(CatalogItem)
    creador_alias = aliased(Usuario)
    revisor_alias = aliased(Usuario)
    aprobador_alias = aliased(Usuario)

    resultado = (
        db.query(
            Documento.codigo,
            Documento.nombre,
            DocumentoVersion.numero_version,
            tipo_item.name.label("tipo"),
            Areas.nombre.label("area"),
            estado_item.name.label("estado"),
            clasificacion_item.name.label("clasificacion"),
            DocumentoVersion.version_id,
            func.to_char(Documento.created_at, 'DD-MM-YY').label("creado"),
            DocumentoVersion.archivo_url.label("url"),
            func.coalesce(func.concat(creador_alias.first_name, ' ', creador_alias.last_name), "pendiente").label(
                "creador"),
            func.coalesce(func.concat(revisor_alias.first_name, ' ', revisor_alias.last_name), "pendiente").label(
                "revisor"),
            func.coalesce(func.concat(aprobador_alias.first_name, ' ', aprobador_alias.last_name), "pendiente").label(
                "aprobador")
        )
        .join(DocumentoVersion, DocumentoVersion.documento_id == Documento.documento_id)
        .join(tipo_item, tipo_item.item_id == Documento.tipo_item_id)
        .join(Areas, Areas.area_id == Documento.area_responsable_item_id)
        .join(clasificacion_item, clasificacion_item.item_id == Documento.clasificacion_item_id)
        .join(estado_item, estado_item.item_id == DocumentoVersion.estado_item_id)
        .join(creador_alias, creador_alias.usuario_id == Documento.creador_id)
        .join(revisor_alias, revisor_alias.usuario_id == DocumentoVersion.revisado_por_id, isouter=True)
        .join(aprobador_alias, aprobador_alias.usuario_id == DocumentoVersion.aprobado_por_id, isouter=True)
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


def create_document_version_service(db: Session, user: dict, document_code: str, document_data: DocumentVersionDto,
                                    file: UploadFile):
    check_auth_and_roles(user, ["admin", "Administrador"])

    if (document_data.creador_id == document_data.revisado_por_id or
            document_data.creador_id == document_data.aprobador_por_id or
            document_data.revisado_por_id == document_data.aprobador_por_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los IDs de creador, revisor y aprobador deben ser diferentes."
        )
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF."
        )
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
        descripcion=document_data.descripcion,
        justificacion=document_data.justificacion,
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
        send_document_notifications(db=db, version_id=new_version.version_id)
        _overlay_pdf_with_status_image(
            db,
            file_url,
            initial_state.item_id,
            signer_name=str(document_data.creador_id),
            fecha=datetime.now()
        )

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear la versión por conflicto de integridad.",
        ) from e

    return f"Versión {new_version_number} del documento creada correctamente"


def send_document_notifications(db: Session, version_id: int):
    # Obtener datos de la versión y usuarios involucrados
    version = db.query(DocumentoVersion).filter(DocumentoVersion.version_id == version_id).first()
    documento = db.query(Documento).filter(Documento.documento_id == version.documento_id).first()
    empresa = db.query(Empresa).filter(Empresa.empresa_id == documento.empresa_id).first()

    revisor = db.query(Usuario).filter(Usuario.usuario_id == version.revisado_por_id).first()
    aprobador = db.query(Usuario).filter(Usuario.usuario_id == version.aprobado_por_id).first()

    # Notificación al revisor
    if revisor:
        notification_revisor = NotificationEmailDto(
            to_email=revisor.email,
            subject=f"Revisión requerida para documento {documento.nombre}",
            accion="Revisar el documento",
            documento=documento.nombre,
            nombre_empresa=empresa.nombre_legal,
            # nombre_usuario=user.get('first_name') + ' ' + user.get('last_name')
            nombre_usuario= revisor.first_name + ' ' + revisor.last_name
        )

        send_email_notification(notification_revisor)

    # Notificación al aprobador
    if aprobador:
        notification_aprobador = NotificationEmailDto(
            to_email=aprobador.email,
            subject=f"Aprobación requerida para documento {documento.nombre}",
            accion="Aprobar el documento",
            documento=documento.nombre,
            nombre_empresa=empresa.nombre_legal,
            nombre_usuario= aprobador.first_name + ' ' + aprobador.last_name
        )
        send_email_notification(notification_aprobador)



def create_comentario_revision_service(db: Session, user: dict, comentario_data: ComentarioRevisionDto):
    usuario_id = user.get('user_id')  # usar la misma clave que el resto del servicio
    if not usuario_id:
        raise HTTPException(status_code=400, detail="Usuario no válido")

    new_comentario = ComentarioRevision(
        version_id=comentario_data.version_id,
        usuario_id=usuario_id,
        comentario=comentario_data.comentario,
        estatus_item_id=comentario_data.status_item_id
    )
    db.add(new_comentario)

    # Actualizar el estado en DocumentoVersion
    version = db.query(DocumentoVersion).filter(DocumentoVersion.version_id == comentario_data.version_id).first()
    if version:
        version.estado_item_id = comentario_data.status_item_id

    try:
        db.commit()
        # después del commit, intentar modificar el PDF en GCS
        try:
            if version and version.archivo_url:
                # pasar el id del usuario como cadena para que _overlay busque por ID
                _overlay_pdf_with_status_image(
                    db,
                    version.archivo_url,
                    comentario_data.status_item_id,
                    signer_name=str(usuario_id),
                    fecha=datetime.now()
                )
        except Exception as e:
            # no silenciar: devolver error claro para depuración
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error al agregar la firma al PDF: {e}")
        return "Comentario creado correctamente"
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear el comentario por conflicto de integridad.",
        ) from e


def get_comentarios_by_version_service(db: Session, version_id: int):
    usuario_alias = aliased(Usuario)
    resultados = (
        db.query(
            ComentarioRevision.comentario,
            func.concat(usuario_alias.first_name, ' ', usuario_alias.last_name).label("usuario"),
            func.to_char(ComentarioRevision.fecha, 'DD-MM-YY HH24:MI').label("fecha")
        )
        .join(usuario_alias, usuario_alias.usuario_id == ComentarioRevision.usuario_id)
        .filter(ComentarioRevision.version_id == version_id)
        .order_by(ComentarioRevision.fecha)
        .all()
    )
    return [dict(r._mapping) for r in resultados]


def _overlay_pdf_with_status_image(db, archivo_url: str, status_item_id: int, signer_name: str = None, fecha: datetime = None):
    if not archivo_url:
        return False

    status_item = db.query(CatalogItem).filter(CatalogItem.item_id == status_item_id).first()
    status_name = (status_item.name or "").lower() if status_item else ""

    # decidir columna: 0 = izquierda, 1 = centro, 2 = derecha
    if "por autorizar" in status_name:
        column = 1
    elif "aprob" in status_name:
        column = 2
    else:
        column = 0

    # Buscar usuario a partir de signer_name
    usuario_obj = None
    if signer_name:
        s = str(signer_name).strip()
        if re.fullmatch(r'\d+', s):
            uid = int(s)
            usuario_obj = db.query(Usuario).filter(Usuario.usuario_id == uid).first()
        else:
            full = func.concat(Usuario.first_name, " ", Usuario.last_name)
            usuario_obj = db.query(Usuario).filter(full == s).first()
            if not usuario_obj:
                usuario_obj = db.query(Usuario).filter(
                    func.concat(Usuario.first_name, " ", Usuario.last_name).ilike(f"%{s}%")).first()

    if not usuario_obj or not usuario_obj.url_firma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no cuenta con firma")

    def _extract_blob_name_from_url(url: str) -> str | None:
        if not url:
            return None
        p = urlparse(url)
        if p.scheme == "gs":
            return p.path.lstrip("/")
        if p.scheme in ("http", "https"):
            path = p.path.lstrip("/")
            netloc = (p.netloc or "")
            if netloc.endswith("storage.googleapis.com"):
                parts = path.split("/", 1)
                if len(parts) == 2:
                    return parts[1]
                return None
            if netloc.endswith(".storage.googleapis.com"):
                return path
            segments = path.split("/")
            if len(segments) >= 4 and segments[0] == "b" and segments[2] == "o":
                return "/".join(segments[3:])
            bucket_name = os.environ.get("BUCKET_NAME")
            if bucket_name and path.startswith(f"{bucket_name}/"):
                return path[len(bucket_name) + 1 :]
            return path
        return url

    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bucket no configurado")

    client = storage.Client()

    # Obtener nombre del blob del PDF normalizando la URL
    pdf_blob_name = _extract_blob_name_from_url(archivo_url)
    if not pdf_blob_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nombre de blob del PDF no válido")

    # Descargar el PDF original
    try:
        bucket = client.bucket(bucket_name)
        pdf_blob = bucket.blob(pdf_blob_name)
        pdf_bytes = pdf_blob.download_as_bytes()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando PDF: {str(e)}"
        )

    # Descargar la imagen de firma
    try:
        firma_blob_name = _extract_blob_name_from_url(usuario_obj.url_firma)
        if not firma_blob_name:
            raise ValueError("Nombre de blob de firma no válido")

        blob_firma = bucket.blob(firma_blob_name)
        signature_bytes = blob_firma.download_as_bytes()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando firma: {str(e)}"
        )

    # Procesar la imagen de firma
    try:


        # Abrir imagen y convertir a RGBA
        img = PILImage.open(io.BytesIO(signature_bytes))

        # Convertir a RGBA si no lo está
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Crear un nuevo fondo transparente
        background = PILImage.new('RGBA', img.size, (255, 255, 255, 0))

        # Combinar imagen con fondo
        img = PILImage.alpha_composite(background, img)

        # Guardar como PNG en buffer (preserva transparencia)
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG', optimize=True)
        img_buffer.seek(0)

        # Crear ImageReader desde el buffer
        img_reader = ImageReader(img_buffer)
        img_w, img_h = img.size

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando imagen de firma: {str(e)}"
        )

    # Procesar el PDF
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if not reader.pages:
            raise ValueError("PDF sin páginas")

        first_page = reader.pages[0]
        media = first_page.mediabox
        page_width = float(media.width)
        page_height = float(media.height)

        left_margin = 40.0  # margen izquierdo en puntos (ajusta para mover todo a la derecha)
        right_margin = 20.0
        column_gap = 2  # px: reducir este valor para disminuir separación entre columnas
        total_gaps = 2 * column_gap
        columns_vertical_shift = 130.0
        available_width = page_width - left_margin - right_margin - total_gaps
        image_scale_factor = 0.6
        column_width = available_width / 3.0
        print(f"Page size: {page_width} x {page_height}")
        max_image_width_pts = column_width * 0.8
        if available_width <= 0:
            raise ValueError("Ancho de página insuficiente para los márgenes/gaps configurados")
        column_width = available_width / 3.0
        print(f"Page size: {page_width} x {page_height}")
        # Calcular dimensiones y posición
        third_width = page_width / 3.0
        print(f"third_width {third_width}")
        target_w = max_image_width_pts * image_scale_factor
        print(f"target_w {target_w}")
        scale = target_w / img_w if img_w else 1.0
        print(f"scale {scale}")
        target_h = img_h * scale
        print(f"target_h {target_h}")

        # Reservar espacio para texto encima de la imagen
        text_space = 36  # espacio total aproximado para nombre y fecha
        bottom_margin = 30  # distancia desde el borde inferior
        y = bottom_margin + columns_vertical_shift
        print(f"y column {y}")
        # Asegurar que imagen + texto quepan en la página; si no, reducir escala
        max_allowed_height = page_height - y - text_space - 10
        if target_h > max_allowed_height and max_allowed_height > 10:
            scale *= max_allowed_height / target_h
            target_h = img_h * scale
            target_w = img_w * scale

        # Posicionar en la columna correspondiente (coordenada X)
        x = left_margin + column * (column_width + column_gap) + (column_width - target_w) / 2.0
        print(f"x column {x}")
        # Y en coordenada de ReportLab: colocar la imagen encima del margen inferior


        # Preparar texto
        fecha = fecha or datetime.now()
        fecha_str = fecha.strftime("%d-%m-%Y %H:%M")

        # if "aprob" in status_name:
        #     label = ""
        # elif "rechaz" in status_name or "no aprobado" in status_name:
        #     label = ""
        # else:
        #     label = ""

        nombre_completo = f"{usuario_obj.first_name} {usuario_obj.last_name}".strip()
        # display_name = f"{label}{nombre_completo}"
        display_name = f"{nombre_completo}"

        # Crear overlay
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # Dibujar imagen en la parte inferior
        c.drawImage(
            img_reader,
            x, y,
            width=target_w,
            height=target_h,
            mask='auto',
            preserveAspectRatio=True
        )

        # Configurar fuente
        font_size = 10
        c.setFont("Helvetica", font_size)

        # Calcular posiciones de texto: colocar encima de la imagen
        text_x = x + target_w / 2.0
        text_y_name = y + target_h + 8
        text_y_date = text_y_name + 12

        # Si el texto supera el alto de la página, reducir tamaño de fuente
        if text_y_date > page_height - 10:
            font_size = 8
            c.setFont("Helvetica", font_size)
            text_y_name = y + target_h + 6
            text_y_date = text_y_name + 10

        # Dibujar textos centrados sobre la imagen
        c.drawCentredString(text_x, text_y_name, display_name)
        c.drawCentredString(text_x, text_y_date, fecha_str)

        c.save()
        packet.seek(0)

        # Merge con PDF original
        overlay_reader = PdfReader(packet)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i == 0:
                page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

        # Guardar resultado
        output = BytesIO()
        writer.write(output)
        output.seek(0)

        # Subir PDF modificado
        pdf_blob.upload_from_file(output, content_type='application/pdf')

        return True

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando PDF: {str(e)}"
        )