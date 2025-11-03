from sqlalchemy.orm import Session

from app.infrastructure.models import Documento


def generar_codigo_documento(db: Session, prefijo: str) -> str:
    # Buscar el último código con el prefijo
    ultimo_documento = (db.query(Documento)
                        .filter(Documento.codigo.like(f"{prefijo}-%"))
                        .order_by(Documento.codigo.desc())
                        .first())
    if ultimo_documento and ultimo_documento.codigo:
        # Extraer el número y sumarle 1
        try:
            ultimo_numero = int(ultimo_documento.codigo.split('-')[1])
        except (IndexError, ValueError):
            ultimo_numero = 0
        nuevo_numero = ultimo_numero + 1
    else:
        nuevo_numero = 1
    # Formatear el nuevo código
    nuevo_codigo = f"{prefijo}-{nuevo_numero:04d}"
    return nuevo_codigo