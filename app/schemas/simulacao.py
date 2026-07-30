from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SimulacaoDetailResponse(BaseModel):
    id: UUID
    tipo: str
    perfil: str
    salario: float
    input_json: dict[str, Any]
    resultado_json: dict[str, Any]
    criado_em: str

    model_config = {"from_attributes": True}
