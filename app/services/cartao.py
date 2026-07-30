from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.margem import calcular_margem_cartao
from app.config import get_settings
from app.enums import Perfil


class CartaoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CartaoResult:
    margem_cartao: Decimal
    limite_credito: Decimal
    valor_minimo_fatura: Decimal


def _round_money(value: Decimal) -> Decimal:
    # Eu uso o mesmo padrão de arredondamento usado em todo o projeto.
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def simular_cartao(salario: Decimal, perfil: Perfil | None = None, limite_multiplicador: Decimal | None = None) -> CartaoResult:
    # Eu mantenho compatibilidade: se não receber multiplicador, uso o das configurações.
    if limite_multiplicador is None:
        limite_multiplicador = get_settings().limite_cartao_multiplicador

    if salario <= 0:
        raise CartaoValidationError("salario deve ser positivo")

    margem = calcular_margem_cartao(salario)
    limite = _round_money(salario * Decimal(limite_multiplicador))

    # Eu determinei que o mínimo da fatura é igual à margem do cartão neste escopo simplificado.
    return CartaoResult(
        margem_cartao=margem,
        limite_credito=limite,
        valor_minimo_fatura=margem,
    )
