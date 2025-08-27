from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from starlette import status
from app.infrastructure.db import get_db

from app.schemas.Dtos.CreateUserRequest import CreateUserRequest, Token

from typing import Annotated

from passlib.context import CryptContext
from app.services.auth_service import create_user, authenticate_user, create_access_token

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]
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
    token = create_access_token(user.email, user.usuario_id, user.last_name, datetime.timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}