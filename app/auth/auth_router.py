from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import csv
from pathlib import Path
from app.auth.utils import verificar_contrasena
from app.auth.auth_handler import crear_token

router = APIRouter()

class LoginInput(BaseModel):
    correo: str
    contrasena: str

@router.post("/login")
def login(data: LoginInput):
    archivo = Path(__file__).parent.parent.parent / "data" / "usuarios.csv"
    with open(archivo, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Correo"] == data.correo:
                if verificar_contrasena(data.contrasena, row["Contrasena"]):
                    token = crear_token(int(row["UsuarioID"]), row["Rol"])
                    return {"access_token": token}
                break
    raise HTTPException(status_code=401, detail="Credenciales inválidas")
