from decimal import Decimal

from app.config import get_settings
from app.enums import Perfil, TipoSimulacao


def test_settings_defaults():
    settings = get_settings()
    assert settings.taxa_juros_mensal == Decimal("0.0179")
    assert settings.limite_cartao_multiplicador == Decimal("1.5")


def test_perfil_values():
    assert Perfil.CLT.value == "CLT"
    assert Perfil.INSS.value == "INSS"
    assert Perfil.SERVIDOR_PUBLICO.value == "SERVIDOR_PUBLICO"


def test_tipo_simulacao_values():
    assert TipoSimulacao.EMPRESTIMO.value == "EMPRESTIMO"
    assert TipoSimulacao.CARTAO.value == "CARTAO"
