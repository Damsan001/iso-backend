from pydantic import BaseModel


class DocumentCreateDto(BaseModel):
    nombre:str
    tipo_item_id:int
    area_responsable_item_id:int
    creador_id:int
    revisado_por_id:int
    aprobado_por_id:int
    clasificacion_item_id:int

    model_config = {'from_attributes': True}

class DocumentVersionDto(BaseModel):

    creador_id:int
    revisado_por_id:int
    aprobador_por_id:int
    descripcion:str
    justificacion:str

    model_config = {'from_attributes': True}

class  ComentarioRevisionDto (BaseModel):
    version_id:int
    comentario:str
    status_item_id:int

    model_config = {'from_attributes': True}

class NotificationEmailDto (BaseModel):
    to_email:str
    subject:str
    accion:str
    documento:str
    nombre_empresa:str
    nombre_usuario:str

    model_config = {'from_attributes': True}