"""create simulacoes table

Revision ID: 001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulacoes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("perfil", sa.String(length=30), nullable=False),
        sa.Column("salario", sa.Numeric(12, 2), nullable=False),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resultado_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_simulacoes_criado_em", "simulacoes", ["criado_em"])


def downgrade() -> None:
    op.drop_index("ix_simulacoes_criado_em", table_name="simulacoes")
    op.drop_table("simulacoes")
