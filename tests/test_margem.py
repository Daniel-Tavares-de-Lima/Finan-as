from decimal import Decimal

import pytest

from app.enums import Perfil
from app.services.margem import (
    calcular_margem_cartao,
    calcular_margem_emprestimo,
    get_percentual_emprestimo,
)


@pytest.mark.parametrize(
    "perfil, salario, expected",
    [
        (Perfil.CLT, Decimal("5000.00"), Decimal("1750.00")),
        (Perfil.INSS, Decimal("1518.00"), Decimal("531.30")),
        (Perfil.SERVIDOR_PUBLICO, Decimal("8000.00"), Decimal("3200.00")),
    ],
)
def test_calcular_margem_emprestimo(perfil, salario, expected):
    assert calcular_margem_emprestimo(salario, perfil) == expected


def test_calcular_margem_cartao_inss():
    assert calcular_margem_cartao(Decimal("1518.00")) == Decimal("75.90")


def test_percentuais_por_perfil():
    assert get_percentual_emprestimo(Perfil.CLT) == Decimal("0.35")
    assert get_percentual_emprestimo(Perfil.INSS) == Decimal("0.35")
    assert get_percentual_emprestimo(Perfil.SERVIDOR_PUBLICO) == Decimal("0.40")
