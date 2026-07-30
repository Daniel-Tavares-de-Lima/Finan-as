from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import Perfil, TipoSimulacao


# Eu defino os modelos Pydantic para requisição/resposta de empréstimo.
# Uso `Decimal` para valores monetários e valido os limites do spec.
class EmprestimoRequest(BaseModel):
    salario: Decimal = Field(gt=0, examples=[5000.00])
    perfil: Perfil
    valor_solicitado: Decimal = Field(gt=0, examples=[10000.00])
    numero_parcelas: int = Field(ge=1, le=96, examples=[24])


# Resposta da simulação; `from_attributes` permite popular direto de objetos ORM.
class EmprestimoResponse(BaseModel):
    id: UUID
    tipo: TipoSimulacao
    perfil: Perfil
    salario: Decimal
    margem_disponivel: Decimal
    valor_solicitado: Decimal
    numero_parcelas: int
    taxa_juros_mensal: Decimal
    valor_parcela: Decimal
    valor_total: Decimal
    cet_mensal: Decimal
    criado_em: datetime

    model_config = {"from_attributes": True}
