from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.infrastructure.db import get_db
from app.services.admin_service import read_all_empresas, search_empresas
from app.services.auth_service import get_current_user

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
router = APIRouter()

@router.get("/roles", status_code=status.HTTP_200_OK)
async def get_roles(db: db_dependency, user: user_dependency):
    # Lógica para obtener todos los roles
    return {"message": "Lista de roles"}
@router.get("/empresas", status_code=status.HTTP_200_OK)
async def get_empresas(db: db_dependency, user: user_dependency):
    empresas = read_all_empresas(db, user)
    return empresas

@router.get("/empresas/{empresa_id}", status_code=status.HTTP_200_OK)
async def get_empresa(empresa_id: int, db: db_dependency, user: user_dependency):
    empresa = search_empresas(db, user, empresa_id)
    return empresa

@router.post("/empresas", status_code=status.HTTP_201_CREATED)
async def create_empresa(db: db_dependency, user: user_dependency):
    # Lógica para crear una nueva empresa
    return {"message": "Empresa creada exitosamente"}