from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.emprestimo import EmprestimoRequest, EmprestimoResponse
from app.services.emprestimo import simular_emprestimo, EmprestimoValidationError
from app.repositories.simulacao import create_simulacao
from app.database import get_db
from app.enums import TipoSimulacao

router = APIRouter()


@router.post("/simulacoes/emprestimo", response_model=EmprestimoResponse, status_code=status.HTTP_201_CREATED)
def criar_emprestimo(request: EmprestimoRequest, db: Session = Depends(get_db)):
    # 1) Tento rodar a simulação; se algo inválido for enviado, retorno 422.
    try:
        resultado = simular_emprestimo(
            salario=request.salario,
            perfil=request.perfil,
            valor_solicitado=request.valor_solicitado,
            numero_parcelas=request.numero_parcelas,
        )
    except EmprestimoValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # 2) Persisto a simulação para histórico/auditoria.
    sim = create_simulacao(
        db=db,
        tipo=TipoSimulacao.EMPRESTIMO,
        perfil=request.perfil,
        salario=request.salario,
        input_json=request.model_dump(),
        resultado_json={
            "margem_disponivel": str(resultado.margem_disponivel),
            "taxa_juros_mensal": str(resultado.taxa_juros_mensal),
            "valor_parcela": str(resultado.valor_parcela),
            "valor_total": str(resultado.valor_total),
            "cet_mensal": str(resultado.cet_mensal),
        },
    )
    db.commit()

    # 3) Montagem da resposta — converto strings/decimais para objetos Pydantic esperados.
    response = {
        "id": sim.id,
        "tipo": sim.tipo,
        "perfil": sim.perfil,
        "salario": sim.salario,
        "margem_disponivel": Decimal(sim.resultado_json["margem_disponivel"]),
        "valor_solicitado": Decimal(sim.input_json.get("valor_solicitado")),
        "numero_parcelas": int(sim.input_json.get("numero_parcelas")),
        "taxa_juros_mensal": Decimal(sim.resultado_json["taxa_juros_mensal"]),
        "valor_parcela": Decimal(sim.resultado_json["valor_parcela"]),
        "valor_total": Decimal(sim.resultado_json["valor_total"]),
        "cet_mensal": Decimal(sim.resultado_json["cet_mensal"]),
        "criado_em": sim.criado_em,
    }

    return response
