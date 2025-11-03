from pydantic import BaseModel


class DocumentCreateDto(BaseModel):
    nombre:str
    tipo_item_id:int
    area_responsable_item_id:int
    creador_id:int
    revisado_por_id:int
    aprobador_por_id:int
    clasificacion_item_id:int

    model_config = {'from_attributes': True}

class DocumentVesionDto(BaseModel):

    creador_id:int
    revisado_por_id:int
    aprobador_por_id:int

    model_config = {'from_attributes': True}