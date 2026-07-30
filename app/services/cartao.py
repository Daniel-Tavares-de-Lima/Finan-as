from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.margem import calcular_margem_cartao


class CartaoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CartaoResult:
    margem_cartao: Decimal
    limite_credito: Decimal
    valor_minimo_fatura: Decimal


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def simular_cartao(salario: Decimal, limite_multiplicador: Decimal) -> CartaoResult:
    if salario <= 0:
        raise CartaoValidationError("salario deve ser positivo")

    margem = calcular_margem_cartao(salario)
    limite = _round_money(salario * limite_multiplicador)

    return CartaoResult(
        margem_cartao=margem,
        limite_credito=limite,
        valor_minimo_fatura=margem,
    )
