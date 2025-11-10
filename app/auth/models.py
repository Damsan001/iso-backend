from pydantic import BaseModel

class Usuario(BaseModel):
    UsuarioID: int
    Correo: str
    Contrasena: str
    Rol: str
