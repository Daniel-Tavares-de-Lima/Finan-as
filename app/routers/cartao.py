from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.cartao import CartaoRequest, CartaoResponse
from app.services.cartao import simular_cartao
from app.repositories.simulacao import create_simulacao
from app.database import get_db
from app.enums import TipoSimulacao

router = APIRouter()


@router.post("/simulacoes/cartao", response_model=CartaoResponse, status_code=status.HTTP_201_CREATED)
def criar_cartao(request: CartaoRequest, db: Session = Depends(get_db)):
    resultado = simular_cartao(salario=request.salario, perfil=request.perfil)

    sim = create_simulacao(
        db=db,
        tipo=TipoSimulacao.CARTAO,
        perfil=request.perfil,
        salario=request.salario,
        input_json=request.model_dump(),
        resultado_json={
            "margem_cartao": str(resultado.margem_cartao),
            "limite_credito": str(resultado.limite_credito),
            "valor_minimo_fatura": str(resultado.valor_minimo_fatura),
        },
    )
    db.commit()

    response = {
        "id": sim.id,
        "tipo": sim.tipo,
        "perfil": sim.perfil,
        "salario": sim.salario,
        "margem_cartao": Decimal(sim.resultado_json["margem_cartao"]),
        "limite_credito": Decimal(sim.resultado_json["limite_credito"]),
        "valor_minimo_fatura": Decimal(sim.resultado_json["valor_minimo_fatura"]),
        "criado_em": sim.criado_em,
    }

    return response
