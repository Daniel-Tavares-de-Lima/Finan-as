from typing import Any
from uuid import UUID

from pydantic import BaseModel


# Eu defino a resposta genérica para GET /simulacoes/{id} — devolvo os JSONs armazenados.
class SimulacaoDetailResponse(BaseModel):
    id: UUID
    tipo: str
    perfil: str
    salario: float
    input_json: dict[str, Any]
    resultado_json: dict[str, Any]
    criado_em: str

    model_config = {"from_attributes": True}
