from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.enums import Perfil
from app.services.margem import calcular_margem_emprestimo


class EmprestimoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class EmprestimoResult:
    margem_disponivel: Decimal
    valor_parcela: Decimal
    valor_total: Decimal
    taxa_juros_mensal: Decimal
    cet_mensal: Decimal


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular_parcela_price(
    valor_solicitado: Decimal, taxa_mensal: Decimal, numero_parcelas: int
) -> Decimal:
    if taxa_mensal == 0:
        return _round_money(valor_solicitado / Decimal(numero_parcelas))
    fator = (Decimal(1) + taxa_mensal) ** numero_parcelas
    parcela = valor_solicitado * (taxa_mensal * fator) / (fator - Decimal(1))
    return _round_money(parcela)


def simular_emprestimo(
    salario: Decimal,
    perfil: Perfil,
    valor_solicitado: Decimal,
    numero_parcelas: int,
    taxa_juros_mensal: Decimal,
) -> EmprestimoResult:
    if not 1 <= numero_parcelas <= 96:
        raise EmprestimoValidationError("numero_parcelas deve estar entre 1 e 96")
    if salario <= 0 or valor_solicitado <= 0:
        raise EmprestimoValidationError("salario e valor_solicitado devem ser positivos")

    margem = calcular_margem_emprestimo(salario, perfil)
    parcela = _calcular_parcela_price(valor_solicitado, taxa_juros_mensal, numero_parcelas)

    if parcela > margem:
        raise EmprestimoValidationError(
            f"valor_parcela ({parcela}) excede a margem disponivel ({margem})"
        )

    valor_total = _round_money(parcela * Decimal(numero_parcelas))

    return EmprestimoResult(
        margem_disponivel=margem,
        valor_parcela=parcela,
        valor_total=valor_total,
        taxa_juros_mensal=taxa_juros_mensal,
        cet_mensal=taxa_juros_mensal,
    )
