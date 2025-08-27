from fastapi import Depends,HTTPException
import os
from datetime import timedelta, timezone,datetime
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.infrastructure.db import get_db
from typing import Annotated
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from jose import jwt, JWTError
from starlette import status
from app.infrastructure.models import Usuario
from app.schemas.Dtos.CreateUserRequest import CreateUserRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

load_dotenv()

db_dependency = Annotated[Session, Depends(get_db)]

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def authenticate_user(email:str, password:str,db):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta = timedelta(minutes=15)):
    encode = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": int(expires.timestamp())})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token:Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Could not validate user.')
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')

def create_user(db: Session, cr_user: CreateUserRequest) -> Usuario:
    email_norm: str = str(cr_user.email).strip().lower()

    # Verificación de unicidad por empresa (case-insensitive)
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

    user = Usuario(
        empresa_id=cr_user.empresa_id,
        area_id=cr_user.area_id,
        first_name=cr_user.first_name,
        last_name=cr_user.last_name,
        email=email_norm,
        hashed_password=bcrypt_context.hash(cr_user.password),
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