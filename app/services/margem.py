from decimal import ROUND_HALF_UP, Decimal

from app.enums import Perfil


# Eu defini os percentuais por perfil — reflito a regra do design spec aqui.
PERCENTUAIS_EMPRESTIMO = {
    Perfil.CLT: Decimal("0.35"),
    Perfil.INSS: Decimal("0.35"),
    Perfil.SERVIDOR_PUBLICO: Decimal("0.40"),
}

PERCENTUAL_CARTAO = Decimal("0.05")


def _round_money(value: Decimal) -> Decimal:
    # Eu uso esta função utilitária para garantir 2 casas com ROUND_HALF_UP.
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_percentual_emprestimo(perfil: Perfil) -> Decimal:
    # Eu retorno o percentual conforme o perfil informado.
    return PERCENTUAIS_EMPRESTIMO[perfil]


def get_percentual_cartao() -> Decimal:
    return PERCENTUAL_CARTAO


def calcular_margem_emprestimo(salario: Decimal, perfil: Perfil) -> Decimal:
    # Eu calculo e arredondo a margem disponível para empréstimo.
    return _round_money(salario * get_percentual_emprestimo(perfil))


def calcular_margem_cartao(salario: Decimal) -> Decimal:
    # Eu calculo e arredondo a margem do cartão (5%).
    return _round_money(salario * PERCENTUAL_CARTAO)
