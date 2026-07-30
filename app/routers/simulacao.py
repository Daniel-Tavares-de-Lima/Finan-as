from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.simulacao import get_simulacao_by_id
from app.database import get_db
from app.schemas.simulacao import SimulacaoDetailResponse

router = APIRouter()


@router.get("/simulacoes/{sim_id}", response_model=SimulacaoDetailResponse)
def get_simulacao(sim_id: UUID, db: Session = Depends(get_db)):
    sim = get_simulacao_by_id(db, str(sim_id))
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulação não encontrada")

    return {
        "id": sim.id,
        "tipo": sim.tipo,
        "perfil": sim.perfil,
        "salario": float(sim.salario),
        "input_json": sim.input_json,
        "resultado_json": sim.resultado_json,
        "criado_em": sim.criado_em.isoformat(),
    }
