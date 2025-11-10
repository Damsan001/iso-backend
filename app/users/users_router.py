from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr
from app.users.users_handler import buscar_usuario_por_correo, actualizar_contrasena
from app.auth.auth_handler import crear_token_temporal, verificar_token_temporal
from fastapi import status
from app.users.users_handler import registrar_usuario, eliminar_usuario

router = APIRouter()


class ResetRequest(BaseModel):
    correo: EmailStr


class ResetPassword(BaseModel):
    token: str
    nueva_contrasena: str


@router.post("/usuarios/solicitar-reset")
def solicitar_reset(data: ResetRequest):
    usuario = buscar_usuario_por_correo(data.correo)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = crear_token_temporal(usuario.UsuarioID)
    # Aquí deberías enviar el token por correo en producción.
    return {"token_temporal": token}


@router.put("/usuarios/{usuario_id}/password")
def resetear_contrasena(usuario_id: int, data: ResetPassword):
    payload = verificar_token_temporal(data.token)
    if not payload or int(payload["sub"]) != usuario_id:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")

    exito = actualizar_contrasena(usuario_id, data.nueva_contrasena)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Contraseña actualizada correctamente"}


class NuevoUsuario(BaseModel):
    correo: EmailStr
    contrasena: constr(min_length=6)
    rol: str


@router.post("/usuarios/", status_code=status.HTTP_201_CREATED)
def crear_usuario(data: NuevoUsuario):
    usuario_id = registrar_usuario(data.correo, data.contrasena, data.rol)
    return {"mensaje": "Usuario creado", "usuario_id": usuario_id}


@router.delete("/usuarios/{usuario_id}")
def eliminar(usuario_id: int):
    exito = eliminar_usuario(usuario_id)
    if not exito:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado"}
