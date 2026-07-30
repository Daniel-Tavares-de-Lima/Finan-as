from enum import Enum


class Perfil(str, Enum):
    CLT = "CLT"
    INSS = "INSS"
    SERVIDOR_PUBLICO = "SERVIDOR_PUBLICO"


class TipoSimulacao(str, Enum):
    EMPRESTIMO = "EMPRESTIMO"
    CARTAO = "CARTAO"
