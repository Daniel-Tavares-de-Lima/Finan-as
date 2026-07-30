import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.enums import Perfil, TipoSimulacao
from app.repositories.simulacao import create_simulacao, get_simulacao_by_id


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_and_get_simulacao(db_session):
    sim = create_simulacao(
        db=db_session,
        tipo=TipoSimulacao.EMPRESTIMO,
        perfil=Perfil.CLT,
        salario=Decimal("5000.00"),
        input_json={"salario": 5000},
        resultado_json={"valor_parcela": 511.06},
    )
    db_session.commit()

    found = get_simulacao_by_id(db_session, sim.id)
    assert found is not None
    assert found.tipo == "EMPRESTIMO"
    assert found.perfil == "CLT"


def test_get_simulacao_not_found(db_session):
    assert get_simulacao_by_id(db_session, uuid.uuid4()) is None
