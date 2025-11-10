from pydantic import BaseModel

class UsuarioResponseDto(BaseModel):
    usuario_id: int
    area_id: int
    empresa_id: int
    first_name: str
    last_name: str
    email: str
    empresa: str
    area: str
    class Config:
        from_attributes = True

class UsuarioResponseDto(BaseModel):
    usuario_id: int
    area_id: int
    empresa_id: int
    first_name: str
    last_name: str
    email: str
    empresa: str
    area: str
    class Config:
        from_attributes = True

class ActivateUserRequest(BaseModel):
    email: str