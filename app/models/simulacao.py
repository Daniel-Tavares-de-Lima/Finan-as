from datetime import datetime
import uuid

from sqlalchemy import DateTime, Index, Numeric, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Simulacao(Base):
    __tablename__ = "simulacoes"
    __table_args__ = (Index("ix_simulacoes_criado_em", "criado_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    salario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    input_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    resultado_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
