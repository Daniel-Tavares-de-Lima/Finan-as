"""Eu escrevi testes para validar a simulação do cartão consignado.

Cobrem casos básicos, INSS e salário inválido.
"""


from decimal import Decimal

import pytest

from app.services.cartao import CartaoValidationError, simular_cartao


def test_simular_cartao_basico():
    result = simular_cartao(
        salario=Decimal("5000.00"),
        limite_multiplicador=Decimal("1.5"),
    )
    assert result.margem_cartao == Decimal("250.00")
    assert result.limite_credito == Decimal("7500.00")
    assert result.valor_minimo_fatura == Decimal("250.00")


def test_simular_cartao_inss():
    result = simular_cartao(
        salario=Decimal("1518.00"),
        limite_multiplicador=Decimal("1.5"),
    )
    assert result.margem_cartao == Decimal("75.90")
    assert result.limite_credito == Decimal("2277.00")


def test_simular_cartao_salario_invalido():
    with pytest.raises(CartaoValidationError):
        simular_cartao(salario=Decimal("0"), limite_multiplicador=Decimal("1.5"))
