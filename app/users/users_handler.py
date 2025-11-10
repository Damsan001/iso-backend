import csv
from pathlib import Path
from typing import Optional
from app.auth.auth_handler import crear_token_temporal, verificar_token_temporal
from app.auth.utils import hash_contrasena, guardar_csv
from app.auth.models import Usuario

RUTA_CSV = Path(__file__).parent.parent.parent / "data" / "usuarios.csv"

def buscar_usuario_por_correo(correo: str) -> Optional[Usuario]:
    with open(RUTA_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Correo"] == correo:
                return Usuario(**row)
    return None

def actualizar_contrasena(usuario_id: int, nueva_contrasena: str) -> bool:
    rows = []
    actualizado = False
    with open(RUTA_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if int(row["UsuarioID"]) == usuario_id:
                row["Contrasena"] = hash_contrasena(nueva_contrasena)
                actualizado = True
            rows.append(row)

    if actualizado:
        guardar_csv(RUTA_CSV, fieldnames, rows)
    return actualizado

def obtener_siguiente_id() -> int:
    with open(RUTA_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        ids = [int(row["UsuarioID"]) for row in reader]
        return max(ids) + 1 if ids else 1

def registrar_usuario(correo: str, contrasena: str, rol: str) -> int:
    nuevo_id = obtener_siguiente_id()
    hashed = hash_contrasena(contrasena)
    nuevo_usuario = {
        "UsuarioID": nuevo_id,
        "Correo": correo,
        "Contrasena": hashed,
        "Rol": rol
    }

    with open(RUTA_CSV, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=nuevo_usuario.keys())
        writer.writerow(nuevo_usuario)

    return nuevo_id

def eliminar_usuario(usuario_id: int) -> bool:
    filas_actualizadas = []
    eliminado = False

    with open(RUTA_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if int(row["UsuarioID"]) != usuario_id:
                filas_actualizadas.append(row)
            else:
                eliminado = True

    if eliminado:
        guardar_csv(RUTA_CSV, fieldnames, filas_actualizadas)

    return eliminado
