from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import Perfil, TipoSimulacao


# Eu defino os modelos Pydantic para requisição/resposta do cartão consignado.
class CartaoRequest(BaseModel):
    salario: Decimal = Field(gt=0, examples=[5000.00])
    perfil: Perfil


# Resposta do cartão — incluo margem, limite e mínimo da fatura.
class CartaoResponse(BaseModel):
    id: UUID
    tipo: TipoSimulacao
    perfil: Perfil
    salario: Decimal
    margem_cartao: Decimal
    limite_credito: Decimal
    valor_minimo_fatura: Decimal
    criado_em: datetime

    model_config = {"from_attributes": True}
