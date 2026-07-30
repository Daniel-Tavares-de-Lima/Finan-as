from enum import Enum


# Defino os perfis suportados pelo simulador.
# Estou usando `str` + `Enum` para que a serialização JSON fique simples.
class Perfil(str, Enum):
    CLT = "CLT"
    INSS = "INSS"
    SERVIDOR_PUBLICO = "SERVIDOR_PUBLICO"


# Tipo de simulação — facilita filtragem/armazenamento.
class TipoSimulacao(str, Enum):
    EMPRESTIMO = "EMPRESTIMO"
    CARTAO = "CARTAO"
