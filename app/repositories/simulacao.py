import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.enums import Perfil, TipoSimulacao
from app.models.simulacao import Simulacao


def create_simulacao(
    db: Session,
    tipo: TipoSimulacao,
    perfil: Perfil,
    salario: Decimal,
    input_json: dict,
    resultado_json: dict,
) -> Simulacao:
    # Eu crio a instância da simulação; uso `.value` dos enums para salvar a string.
    # Chamo `flush()` para garantir que `id` e outros defaults estejam disponíveis.
    simulacao = Simulacao(
        id=str(uuid.uuid4()),
        tipo=tipo.value,
        perfil=perfil.value,
        salario=salario,
        input_json=input_json,
        resultado_json=resultado_json,
    )
    db.add(simulacao)
    db.flush()
    return simulacao


def get_simulacao_by_id(db: Session, simulacao_id: uuid.UUID | str):
    # Eu normalizo para string e uso `Session.get` para recuperar por PK.
    key = str(simulacao_id)
    return db.get(Simulacao, key)
