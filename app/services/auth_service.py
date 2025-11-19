import uuid

from fastapi import Depends, HTTPException, BackgroundTasks, UploadFile
import os
from datetime import timedelta, timezone,datetime
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.infrastructure.db import get_db
from typing import Annotated, List
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from jose import jwt, JWTError
from starlette import status
from app.infrastructure.models import Usuario, Rol, Permiso, UsuarioPermiso, RolPermiso, Empresa, Areas, usuario_rol
from app.schemas.Dtos.CreateUserRequest import CreateUserRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.services.google_cloud_aservice import upload_file_to_gcs
from app.utils.send_email import send_email_password

load_dotenv()

db_dependency = Annotated[Session, Depends(get_db)]

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def _truncate_password(password: str) -> str:

    password_bytes = password.encode('utf-8')[:72]
    return password_bytes.decode('utf-8', errors='ignore')


def authenticate_user(email: str, password: str, db):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        return False
    password = _truncate_password(password)
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(*, payload: dict, expires_delta: timedelta | None = timedelta(minutes=15)) -> str:
    to_encode = payload.copy()
    expires = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": int(expires.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token:Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        user_id: int = payload.get("sub")
        first_name: str = payload.get("first_name")
        last_name: str = payload.get("last_name")
        active: bool = payload.get("activo")
        empresa_id: int = payload.get("empresa_id")
        area_id: int = payload.get("area_id")
        roles: List[str] = payload.get("roles", [])
        permisos: List[str] = payload.get("permisos", [])
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Could not validate user.')
        if not active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user.')
        return {
            'user_id': user_id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'empresa_id': empresa_id,
            'area_id': area_id,
            'activo': active,
            'roles': roles,
            'permisos': permisos
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')

def create_user(db: Session, cr_user: CreateUserRequest) -> Usuario:
    email_norm: str = str(cr_user.email).strip().lower()


    exists = (
        db.query(Usuario)
        .filter(
            (Usuario.empresa_id == cr_user.empresa_id) &
            (func.lower(Usuario.email) == email_norm)
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado para esta empresa.",
        )

    hashed_password = bcrypt_context.hash(_truncate_password(cr_user.password))
    user = Usuario(
        empresa_id=cr_user.empresa_id,
        area_id=cr_user.area_id,
        first_name=cr_user.first_name,
        last_name=cr_user.last_name,
        email=email_norm,
        hashed_password=hashed_password,
        activo=False,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Respaldo ante colisión con índice único en BD
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear el usuario por correo duplicado.",
        ) from e

    db.refresh(user)
    return user

def buscar_usuarios(db: Session, usuario_id: int | None = None):
    query = (
        db.query(
            Usuario.usuario_id,
            Areas.area_id,
            Empresa.empresa_id,
            Usuario.first_name,
            Usuario.last_name,
            Usuario.email,
            Empresa.nombre_legal.label("empresa"),
            Areas.nombre.label("area")
        )
        .join(Empresa, Usuario.empresa_id == Empresa.empresa_id)
        .join(Areas, Usuario.area_id == Areas.area_id)
    )
    if usuario_id is not None:
        query = query.filter(Usuario.usuario_id == usuario_id)
    return [dict(row._mapping) for row in query.all()]

def obtener_roles_usuario(db: Session, usuario_id: int) -> list[str]:
    roles = (
        db.query(Rol.nombre)
        .join(usuario_rol, Rol.rol_id == usuario_rol.c.rol_id)
        .filter(
            usuario_rol.c.usuario_id == usuario_id,
            Rol.activo.is_(True)
        )
        .all()
    )
    return [str(r[0]) for r in roles]

def obtener_permisos_usuario(db: Session, usuario_id: int) -> list[str]:
    permisos = (
        db.query(Permiso.codigo)
        .distinct()
        .join(UsuarioPermiso, Permiso.permiso_id == UsuarioPermiso.permiso_id)
        .join(usuario_rol, UsuarioPermiso.usuario_id == usuario_rol.c.usuario_id)
        .join(RolPermiso, usuario_rol.c.rol_id == RolPermiso.rol_id)
        .filter(
            (UsuarioPermiso.usuario_id == usuario_id) & (UsuarioPermiso.concedido.is_(True)) |
            (usuario_rol.c.usuario_id == usuario_id)
        )
        .all()
    )
    return [str(p[0]) for p in permisos]

def reset_password_service(token: str, new_password: str, confirm_password: str, db: Session):
    print(f"[DEBUG] Token recibido para reset: {token}")  # Log para depuración
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    user = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.hashed_password = bcrypt_context.hash(_truncate_password(new_password))
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}

def activate_user(db: Session,user: dict, email: str):
    ensure_authenticated(user)
    required_roles = ["Administrador"]
    ensure_user_roles(user, required_roles)

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if user.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya está activo.")
    user.activo = True
    db.commit()
    db.refresh(user)
    return {"mensaje": "Usuario activado exitosamente."}

def ensure_authenticated(user: dict):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
def ensure_user_roles(user: dict, roles: List[str]):
    if not any(role in roles for role in user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

def check_auth_and_roles(user: dict, required_roles: list[str]):
    ensure_authenticated(user)
    ensure_user_roles(user, required_roles)

def forgot_password_service(email: str, db: Session, background_tasks: BackgroundTasks, url_site: str):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        return {"mensaje": "Si el correo existe, se enviará un enlace de recuperación."}
    token = create_access_token(payload={"sub": str(user.usuario_id), "email": user.email}, expires_delta=timedelta(hours=1))
    reset_url = f"{url_site}/reset-password?data={token}"
    background_tasks.add_task(send_email_password, email, reset_url)
    return {"mensaje": "Si el correo existe, se enviará un enlace de recuperación."}

def upload_firma_service(db: Session, user: dict, file: UploadFile) -> str:
    """
    Sube una imagen de firma a GCS y guarda la URL en Usuario.url_firma.
    Retorna la URL pública.
    """
    # autenticación/validación simple
    if user is None or user.get("user_id") is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    if file is None or not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo debe ser una imagen")

    usuario_id = user.get("user_id")

    # generar nombre único para el blob
    original_name = os.path.basename(file.filename or "firma")
    unique_name = f"{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex}_{original_name}"
    destination_blob = f"firmas/{usuario_id}/{unique_name}"

    try:
        public_url = upload_file_to_gcs(file, destination_blob)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error subiendo imagen a almacenamiento") from e

    # actualizar registro del usuario
    db_user = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_user.url_firma = public_url
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error guardando URL en el usuario") from e

    return public_url
