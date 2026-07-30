from decimal import Decimal

import pytest

from app.enums import Perfil
from app.services.emprestimo import EmprestimoValidationError, simular_emprestimo


def test_simular_emprestimo_clt_sucesso():
    result = simular_emprestimo(
        salario=Decimal("5000.00"),
        perfil=Perfil.CLT,
        valor_solicitado=Decimal("10000.00"),
        numero_parcelas=24,
        taxa_juros_mensal=Decimal("0.0179"),
    )
    assert result.margem_disponivel == Decimal("1750.00")
    assert result.valor_parcela == Decimal("511.06")
    assert result.valor_total == Decimal("12265.44")
    assert result.taxa_juros_mensal == Decimal("0.0179")
    assert result.cet_mensal == Decimal("0.0179")


def test_simular_emprestimo_parcela_excede_margem():
    with pytest.raises(EmprestimoValidationError, match="excede a margem"):
        simular_emprestimo(
            salario=Decimal("2000.00"),
            perfil=Perfil.CLT,
            valor_solicitado=Decimal("50000.00"),
            numero_parcelas=12,
            taxa_juros_mensal=Decimal("0.0179"),
        )


def test_simular_emprestimo_parcelas_invalidas():
    with pytest.raises(EmprestimoValidationError, match="numero_parcelas"):
        simular_emprestimo(
            salario=Decimal("5000.00"),
            perfil=Perfil.CLT,
            valor_solicitado=Decimal("1000.00"),
            numero_parcelas=0,
            taxa_juros_mensal=Decimal("0.0179"),
        )
