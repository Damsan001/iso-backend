from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from app.infrastructure.db import get_db
from app.schemas.Dtos.UsuarioResponseDto import UsuarioResponseDto, ActivateUserRequest

from app.schemas.Dtos.CreateUserRequest import CreateUserRequest, Token

from typing import Annotated

from passlib.context import CryptContext
from app.services.auth_service import create_user, authenticate_user, create_access_token, get_current_user, \
    buscar_usuarios, obtener_permisos_usuario, obtener_roles_usuario,activate_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
@router.post("/user", status_code=status.HTTP_201_CREATED)
# Mostrar o secret key e o algoritmo
async def create_user_endpoint(db: db_dependency, cr_user: CreateUserRequest):
    created_user = create_user(db, cr_user)
    return created_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    permisos = obtener_permisos_usuario(db, user.usuario_id)
    roles = obtener_roles_usuario(db, user.usuario_id)
    payload = {
        "sub": str(user.usuario_id),
        "email": user.email,
        "last_name": user.last_name,
        "empresa_id": user.empresa_id,
        "area_id": user.area_id,
        "activo": user.activo,
        "roles": roles,
        "permisos": permisos
    }
    token = create_access_token(payload=payload, expires_delta=datetime.timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/user", status_code= status.HTTP_200_OK)
async def read_users_me( user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    usuario = buscar_usuarios(db, user["user_id"])
    usuarios_dto = [UsuarioResponseDto(**u).dict() for u in usuario]
    roles = obtener_roles_usuario(db, user["user_id"])
    permisos = obtener_permisos_usuario(db, user["user_id"])
    return {
        "usuario": usuarios_dto,
        "roles": roles,
        "permisos": permisos
    }

@router.put("/activate", status_code=status.HTTP_200_OK)
async def activate_user_account(
    db: db_dependency,
    user: user_dependency,
    request: ActivateUserRequest
):
    activate_user(db, user, request.email)
    return {"message": f"User account with email {request.email} has been activated."}