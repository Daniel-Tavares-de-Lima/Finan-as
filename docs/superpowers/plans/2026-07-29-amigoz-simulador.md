# Amigoz Simulador Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI API that simulates empréstimo consignado and cartão consignado for all profiles (CLT, INSS, Servidor Público), persists simulations in PostgreSQL, and ships with tests, Docker Compose, and GitHub Actions CI.

**Architecture:** Monolithic layered FastAPI app (`routers → services → repositories → models`) with a shared margem service for profile-based business rules. PostgreSQL persistence via SQLAlchemy 2.0 + Alembic migrations.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16, pytest, httpx, ruff, Docker Compose, GitHub Actions

## Global Constraints

- Profiles: `CLT`, `INSS`, `SERVIDOR_PUBLICO` only
- Margem empréstimo: CLT 35%, INSS 35%, Servidor Público 40%
- Margem cartão: 5% for all profiles
- No margem comprometida — assume 100% free margin
- Taxa juros empréstimo: `TAXA_JUROS_MENSAL=0.0179` (env, default 1.79% a.m.)
- Amortização: Tabela Price (parcelas fixas)
- Limite cartão: `LIMITE_CARTAO_MULTIPLICADOR=1.5` (env, default 1.5× salário)
- Parcelas empréstimo: 1–96 inclusive
- Reject empréstimo with HTTP 422 when `valor_parcela > margem_disponivel`
- CET mensal = taxa juros mensal (no IOF/tarifas)
- Persist simulations only (no user registration)
- API base path: `/api/v1`
- README language: português
- Monetary values rounded to 2 decimal places

---

## File Map

| File | Responsibility |
|---|---|
| `app/config.py` | Pydantic Settings (DATABASE_URL, taxa, multiplicador) |
| `app/enums.py` | `Perfil`, `TipoSimulacao` enums |
| `app/services/margem.py` | Margin percentages and calculations by profile |
| `app/services/emprestimo.py` | Price table calculation + validation |
| `app/services/cartao.py` | Credit limit and minimum invoice calculation |
| `app/models/simulacao.py` | SQLAlchemy `Simulacao` model |
| `app/database.py` | Engine, session factory, `get_db` dependency |
| `app/repositories/simulacao.py` | Create and fetch simulations |
| `app/schemas/emprestimo.py` | Pydantic request/response for empréstimo |
| `app/schemas/cartao.py` | Pydantic request/response for cartão |
| `app/schemas/simulacao.py` | Shared GET response schema |
| `app/routers/emprestimo.py` | POST `/simulacoes/emprestimo` |
| `app/routers/cartao.py` | POST `/simulacoes/cartao` |
| `app/routers/simulacao.py` | GET `/simulacoes/{id}` |
| `app/routers/health.py` | GET `/health` |
| `app/main.py` | FastAPI app, lifespan, router registration |
| `alembic/` | DB migrations |
| `docker-compose.yml` | PostgreSQL + API |
| `Dockerfile` | API container |
| `.github/workflows/ci.yml` | Lint + test pipeline |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `.gitignore`, `.env.example`, `app/__init__.py`

**Interfaces:**
- Produces: project skeleton with pinned dependencies

- [ ] **Step 1: Initialize git repository**

```bash
git init
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.py[cod]
.env
.venv/
venv/
.pytest_cache/
.ruff_cache/
*.egg-info/
dist/
build/
.coverage
htmlcov/
```

- [ ] **Step 3: Create `requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic-settings==2.7.0
```

- [ ] **Step 4: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest==8.3.4
httpx==0.28.1
ruff==0.8.4
```

- [ ] **Step 5: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- [ ] **Step 6: Create `.env.example`**

```
DATABASE_URL=postgresql://simulador:simulador@localhost:5432/simulador
TAXA_JUROS_MENSAL=0.0179
LIMITE_CARTAO_MULTIPLICADOR=1.5
APP_ENV=development
```

- [ ] **Step 7: Create empty package**

```bash
mkdir -p app/services app/routers app/repositories app/models app/schemas tests
touch app/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "chore: initialize project scaffolding"
```

---

### Task 2: Config and Enums

**Files:**
- Create: `app/config.py`, `app/enums.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `Settings` class, `Perfil` enum, `TipoSimulacao` enum

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `app/enums.py`:

```python
from enum import Enum


class Perfil(str, Enum):
    CLT = "CLT"
    INSS = "INSS"
    SERVIDOR_PUBLICO = "SERVIDOR_PUBLICO"


class TipoSimulacao(str, Enum):
    EMPRESTIMO = "EMPRESTIMO"
    CARTAO = "CARTAO"
```

Create `app/config.py`:

```python
from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://simulador:simulador@localhost:5432/simulador"
    taxa_juros_mensal: Decimal = Decimal("0.0179")
    limite_cartao_multiplicador: Decimal = Decimal("1.5")
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/enums.py tests/test_config.py
git commit -m "feat: add config and enums"
```

---

### Task 3: Margem Service

**Files:**
- Create: `app/services/margem.py`, `tests/test_margem.py`

**Interfaces:**
- Consumes: `Perfil` from `app.enums`
- Produces:
  - `get_percentual_emprestimo(perfil: Perfil) -> Decimal`
  - `get_percentual_cartao() -> Decimal` (always 0.05)
  - `calcular_margem_emprestimo(salario: Decimal, perfil: Perfil) -> Decimal`
  - `calcular_margem_cartao(salario: Decimal) -> Decimal`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_margem.py`:

```python
from decimal import Decimal

import pytest

from app.enums import Perfil
from app.services.margem import (
    calcular_margem_cartao,
    calcular_margem_emprestimo,
    get_percentual_emprestimo,
)


@pytest.mark.parametrize(
    "perfil, salario, expected",
    [
        (Perfil.CLT, Decimal("5000.00"), Decimal("1750.00")),
        (Perfil.INSS, Decimal("1518.00"), Decimal("531.30")),
        (Perfil.SERVIDOR_PUBLICO, Decimal("8000.00"), Decimal("3200.00")),
    ],
)
def test_calcular_margem_emprestimo(perfil, salario, expected):
    assert calcular_margem_emprestimo(salario, perfil) == expected


def test_calcular_margem_cartao_inss():
    assert calcular_margem_cartao(Decimal("1518.00")) == Decimal("75.90")


def test_percentuais_por_perfil():
    assert get_percentual_emprestimo(Perfil.CLT) == Decimal("0.35")
    assert get_percentual_emprestimo(Perfil.INSS) == Decimal("0.35")
    assert get_percentual_emprestimo(Perfil.SERVIDOR_PUBLICO) == Decimal("0.40")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_margem.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `app/services/margem.py`:

```python
from decimal import ROUND_HALF_UP, Decimal

from app.enums import Perfil

PERCENTUAIS_EMPRESTIMO = {
    Perfil.CLT: Decimal("0.35"),
    Perfil.INSS: Decimal("0.35"),
    Perfil.SERVIDOR_PUBLICO: Decimal("0.40"),
}

PERCENTUAL_CARTAO = Decimal("0.05")


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_percentual_emprestimo(perfil: Perfil) -> Decimal:
    return PERCENTUAIS_EMPRESTIMO[perfil]


def get_percentual_cartao() -> Decimal:
    return PERCENTUAL_CARTAO


def calcular_margem_emprestimo(salario: Decimal, perfil: Perfil) -> Decimal:
    return _round_money(salario * get_percentual_emprestimo(perfil))


def calcular_margem_cartao(salario: Decimal) -> Decimal:
    return _round_money(salario * PERCENTUAL_CARTAO)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_margem.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/margem.py tests/test_margem.py
git commit -m "feat: add margem consignavel service"
```

---

### Task 4: Empréstimo Service (Price)

**Files:**
- Create: `app/services/emprestimo.py`, `tests/test_emprestimo.py`

**Interfaces:**
- Consumes: `calcular_margem_emprestimo`, `Perfil`, `Settings.taxa_juros_mensal`
- Produces:
  - `EmprestimoResult` dataclass with fields: `margem_disponivel`, `valor_parcela`, `valor_total`, `taxa_juros_mensal`, `cet_mensal`
  - `simular_emprestimo(salario, perfil, valor_solicitado, numero_parcelas, taxa_juros_mensal) -> EmprestimoResult`
  - Raises `EmprestimoValidationError` when parcela exceeds margem or parcelas out of range

- [ ] **Step 1: Write the failing tests**

Create `tests/test_emprestimo.py`:

```python
from decimal import Decimal

import pytest

from app.enums import Perfil
from app.services.emprestimo import EmprestimoValidationError, simular_emprestimo


def test_simular_emprestimo_clt_sucesso():
    result = simular_emprestimo(
        salario=Decimal("5000.00"),
        perfil=Perfil.CLT,
        valor_solicitado=Decimal("10000.00"),
        numero_parcelas=24,
        taxa_juros_mensal=Decimal("0.0179"),
    )
    assert result.margem_disponivel == Decimal("1750.00")
    assert result.valor_parcela == Decimal("511.06")
    assert result.valor_total == Decimal("12265.44")
    assert result.taxa_juros_mensal == Decimal("0.0179")
    assert result.cet_mensal == Decimal("0.0179")


def test_simular_emprestimo_parcela_excede_margem():
    with pytest.raises(EmprestimoValidationError, match="excede a margem"):
        simular_emprestimo(
            salario=Decimal("2000.00"),
            perfil=Perfil.CLT,
            valor_solicitado=Decimal("50000.00"),
            numero_parcelas=12,
            taxa_juros_mensal=Decimal("0.0179"),
        )


def test_simular_emprestimo_parcelas_invalidas():
    with pytest.raises(EmprestimoValidationError, match="numero_parcelas"):
        simular_emprestimo(
            salario=Decimal("5000.00"),
            perfil=Perfil.CLT,
            valor_solicitado=Decimal("1000.00"),
            numero_parcelas=0,
            taxa_juros_mensal=Decimal("0.0179"),
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_emprestimo.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `app/services/emprestimo.py`:

```python
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.enums import Perfil
from app.services.margem import calcular_margem_emprestimo


class EmprestimoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class EmprestimoResult:
    margem_disponivel: Decimal
    valor_parcela: Decimal
    valor_total: Decimal
    taxa_juros_mensal: Decimal
    cet_mensal: Decimal


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular_parcela_price(
    valor_solicitado: Decimal, taxa_mensal: Decimal, numero_parcelas: int
) -> Decimal:
    if taxa_mensal == 0:
        return _round_money(valor_solicitado / numero_parcelas)
    fator = (1 + taxa_mensal) ** numero_parcelas
    parcela = valor_solicitado * (taxa_mensal * fator) / (fator - 1)
    return _round_money(parcela)


def simular_emprestimo(
    salario: Decimal,
    perfil: Perfil,
    valor_solicitado: Decimal,
    numero_parcelas: int,
    taxa_juros_mensal: Decimal,
) -> EmprestimoResult:
    if not 1 <= numero_parcelas <= 96:
        raise EmprestimoValidationError("numero_parcelas deve estar entre 1 e 96")
    if salario <= 0 or valor_solicitado <= 0:
        raise EmprestimoValidationError("salario e valor_solicitado devem ser positivos")

    margem = calcular_margem_emprestimo(salario, perfil)
    parcela = _calcular_parcela_price(valor_solicitado, taxa_juros_mensal, numero_parcelas)

    if parcela > margem:
        raise EmprestimoValidationError(
            f"valor_parcela ({parcela}) excede a margem disponivel ({margem})"
        )

    valor_total = _round_money(parcela * numero_parcelas)

    return EmprestimoResult(
        margem_disponivel=margem,
        valor_parcela=parcela,
        valor_total=valor_total,
        taxa_juros_mensal=taxa_juros_mensal,
        cet_mensal=taxa_juros_mensal,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_emprestimo.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/emprestimo.py tests/test_emprestimo.py
git commit -m "feat: add emprestimo simulation with Price table"
```

---

### Task 5: Cartão Service

**Files:**
- Create: `app/services/cartao.py`, `tests/test_cartao.py`

**Interfaces:**
- Consumes: `calcular_margem_cartao`, `Settings.limite_cartao_multiplicador`
- Produces:
  - `CartaoResult` dataclass: `margem_cartao`, `limite_credito`, `valor_minimo_fatura`
  - `simular_cartao(salario, limite_multiplicador) -> CartaoResult`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cartao.py`:

```python
from decimal import Decimal

import pytest

from app.services.cartao import CartaoValidationError, simular_cartao


def test_simular_cartao_basico():
    result = simular_cartao(
        salario=Decimal("5000.00"),
        limite_multiplicador=Decimal("1.5"),
    )
    assert result.margem_cartao == Decimal("250.00")
    assert result.limite_credito == Decimal("7500.00")
    assert result.valor_minimo_fatura == Decimal("250.00")


def test_simular_cartao_inss():
    result = simular_cartao(
        salario=Decimal("1518.00"),
        limite_multiplicador=Decimal("1.5"),
    )
    assert result.margem_cartao == Decimal("75.90")
    assert result.limite_credito == Decimal("2277.00")


def test_simular_cartao_salario_invalido():
    with pytest.raises(CartaoValidationError):
        simular_cartao(salario=Decimal("0"), limite_multiplicador=Decimal("1.5"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cartao.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `app/services/cartao.py`:

```python
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.margem import calcular_margem_cartao


class CartaoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CartaoResult:
    margem_cartao: Decimal
    limite_credito: Decimal
    valor_minimo_fatura: Decimal


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def simular_cartao(salario: Decimal, limite_multiplicador: Decimal) -> CartaoResult:
    if salario <= 0:
        raise CartaoValidationError("salario deve ser positivo")

    margem = calcular_margem_cartao(salario)
    limite = _round_money(salario * limite_multiplicador)

    return CartaoResult(
        margem_cartao=margem,
        limite_credito=limite,
        valor_minimo_fatura=margem,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cartao.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/cartao.py tests/test_cartao.py
git commit -m "feat: add cartao consignado simulation"
```

---

### Task 6: Database Layer

**Files:**
- Create: `app/database.py`, `app/models/simulacao.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/001_create_simulacoes.py`

**Interfaces:**
- Consumes: `Settings.database_url`, `Perfil`, `TipoSimulacao`
- Produces:
  - `Simulacao` SQLAlchemy model
  - `get_db()` FastAPI dependency yielding `Session`
  - Alembic migration creating `simulacoes` table

- [ ] **Step 1: Create database module**

Create `app/database.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
```

- [ ] **Step 2: Create model**

Create `app/models/simulacao.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Simulacao(Base):
    __tablename__ = "simulacoes"
    __table_args__ = (Index("ix_simulacoes_criado_em", "criado_em"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    salario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    input_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    resultado_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 3: Initialize Alembic and write migration**

```bash
pip install -r requirements-dev.txt
alembic init alembic
```

Replace `alembic/env.py` key sections:

```python
from app.config import get_settings
from app.database import Base
from app.models.simulacao import Simulacao  # noqa: F401

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata
```

Create `alembic/versions/001_create_simulacoes.py`:

```python
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
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("perfil", sa.String(30), nullable=False),
        sa.Column("salario", sa.Numeric(12, 2), nullable=False),
        sa.Column("input_json", postgresql.JSONB, nullable=False),
        sa.Column("resultado_json", postgresql.JSONB, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_simulacoes_criado_em", "simulacoes", ["criado_em"])


def downgrade() -> None:
    op.drop_index("ix_simulacoes_criado_em", table_name="simulacoes")
    op.drop_table("simulacoes")
```

- [ ] **Step 4: Run migration against local PostgreSQL**

Run: `alembic upgrade head`
Expected: migration applies without error (requires PostgreSQL running)

- [ ] **Step 5: Commit**

```bash
git add app/database.py app/models/ alembic/ alembic.ini
git commit -m "feat: add database layer and alembic migration"
```

---

### Task 7: Simulation Repository

**Files:**
- Create: `app/repositories/simulacao.py`, `tests/test_repository.py`

**Interfaces:**
- Consumes: `Simulacao` model, SQLAlchemy `Session`
- Produces:
  - `create_simulacao(db, tipo, perfil, salario, input_json, resultado_json) -> Simulacao`
  - `get_simulacao_by_id(db, simulacao_id: UUID) -> Simulacao | None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_repository.py`:

```python
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
```

Note: SQLite used in unit test for repository isolation; CI uses PostgreSQL.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_repository.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `app/repositories/simulacao.py`:

```python
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
    simulacao = Simulacao(
        id=uuid.uuid4(),
        tipo=tipo.value,
        perfil=perfil.value,
        salario=salario,
        input_json=input_json,
        resultado_json=resultado_json,
    )
    db.add(simulacao)
    db.flush()
    return simulacao


def get_simulacao_by_id(db: Session, simulacao_id: uuid.UUID) -> Simulacao | None:
    return db.get(Simulacao, simulacao_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_repository.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/repositories/simulacao.py tests/test_repository.py
git commit -m "feat: add simulation repository"
```

---

### Task 8: Pydantic Schemas

**Files:**
- Create: `app/schemas/emprestimo.py`, `app/schemas/cartao.py`, `app/schemas/simulacao.py`

**Interfaces:**
- Consumes: `Perfil`, `TipoSimulacao`
- Produces: Request/response models used by routers

- [ ] **Step 1: Create schemas**

Create `app/schemas/emprestimo.py`:

```python
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import Perfil, TipoSimulacao


class EmprestimoRequest(BaseModel):
    salario: Decimal = Field(gt=0, examples=[5000.00])
    perfil: Perfil
    valor_solicitado: Decimal = Field(gt=0, examples=[10000.00])
    numero_parcelas: int = Field(ge=1, le=96, examples=[24])


class EmprestimoResponse(BaseModel):
    id: UUID
    tipo: TipoSimulacao
    perfil: Perfil
    salario: Decimal
    margem_disponivel: Decimal
    valor_solicitado: Decimal
    numero_parcelas: int
    taxa_juros_mensal: Decimal
    valor_parcela: Decimal
    valor_total: Decimal
    cet_mensal: Decimal
    criado_em: datetime

    model_config = {"from_attributes": True}
```

Create `app/schemas/cartao.py`:

```python
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import Perfil, TipoSimulacao


class CartaoRequest(BaseModel):
    salario: Decimal = Field(gt=0, examples=[5000.00])
    perfil: Perfil


class CartaoResponse(BaseModel):
    id: UUID
    tipo: TipoSimulacao
    perfil: Perfil
    salario: Decimal
    margem_cartao: Decimal
    limite_credito: Decimal
    valor_minimo_fatura: Decimal
    criado_em: datetime

    model_config = {"from_attributes": True}
```

Create `app/schemas/simulacao.py`:

```python
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SimulacaoDetailResponse(BaseModel):
    id: UUID
    tipo: str
    perfil: str
    salario: float
    input_json: dict[str, Any]
    resultado_json: dict[str, Any]
    criado_em: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add app/schemas/
git commit -m "feat: add pydantic schemas"
```

---

### Task 9: API Routers and Main App

**Files:**
- Create: `app/routers/emprestimo.py`, `app/routers/cartao.py`, `app/routers/simulacao.py`, `app/routers/health.py`, `app/main.py`, `tests/test_api.py`, `tests/conftest.py`

**Interfaces:**
- Consumes: all services, repository, schemas, `get_db`, `get_settings`
- Produces: working FastAPI app with all endpoints

- [ ] **Step 1: Write failing API tests**

Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Create `tests/test_api.py`:

```python
import uuid


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simular_emprestimo(client):
    response = client.post(
        "/api/v1/simulacoes/emprestimo",
        json={
            "salario": 5000.00,
            "perfil": "CLT",
            "valor_solicitado": 10000.00,
            "numero_parcelas": 24,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["margem_disponivel"] == 1750.00
    assert data["valor_parcela"] == 511.06
    sim_id = data["id"]

    get_response = client.get(f"/api/v1/simulacoes/{sim_id}")
    assert get_response.status_code == 200


def test_simular_emprestimo_parcela_excede_margem(client):
    response = client.post(
        "/api/v1/simulacoes/emprestimo",
        json={
            "salario": 2000.00,
            "perfil": "CLT",
            "valor_solicitado": 50000.00,
            "numero_parcelas": 12,
        },
    )
    assert response.status_code == 422


def test_simular_cartao(client):
    response = client.post(
        "/api/v1/simulacoes/cartao",
        json={"salario": 1518.00, "perfil": "INSS"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["margem_cartao"] == 75.90
    assert data["limite_credito"] == 2277.00


def test_get_simulacao_not_found(client):
    response = client.get(f"/api/v1/simulacoes/{uuid.uuid4()}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL (app not defined)

- [ ] **Step 3: Implement routers and main app**

Create `app/routers/health.py`:

```python
from fastapi import APIRouter

from app.database import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_status = "connected"
    try:
        check_database_connection()
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "database": db_status}
```

Create `app/routers/emprestimo.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.enums import TipoSimulacao
from app.repositories.simulacao import create_simulacao
from app.schemas.emprestimo import EmprestimoRequest, EmprestimoResponse
from app.services.emprestimo import EmprestimoValidationError, simular_emprestimo

router = APIRouter(prefix="/api/v1/simulacoes", tags=["emprestimo"])


@router.post("/emprestimo", response_model=EmprestimoResponse, status_code=201)
def criar_simulacao_emprestimo(
    body: EmprestimoRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        result = simular_emprestimo(
            salario=body.salario,
            perfil=body.perfil,
            valor_solicitado=body.valor_solicitado,
            numero_parcelas=body.numero_parcelas,
            taxa_juros_mensal=settings.taxa_juros_mensal,
        )
    except EmprestimoValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    resultado = {
        "margem_disponivel": float(result.margem_disponivel),
        "valor_solicitado": float(body.valor_solicitado),
        "numero_parcelas": body.numero_parcelas,
        "taxa_juros_mensal": float(result.taxa_juros_mensal),
        "valor_parcela": float(result.valor_parcela),
        "valor_total": float(result.valor_total),
        "cet_mensal": float(result.cet_mensal),
    }

    sim = create_simulacao(
        db=db,
        tipo=TipoSimulacao.EMPRESTIMO,
        perfil=body.perfil,
        salario=body.salario,
        input_json=body.model_dump(mode="json"),
        resultado_json=resultado,
    )
    db.commit()

    return EmprestimoResponse(
        id=sim.id,
        tipo=TipoSimulacao.EMPRESTIMO,
        perfil=body.perfil,
        salario=body.salario,
        margem_disponivel=result.margem_disponivel,
        valor_solicitado=body.valor_solicitado,
        numero_parcelas=body.numero_parcelas,
        taxa_juros_mensal=result.taxa_juros_mensal,
        valor_parcela=result.valor_parcela,
        valor_total=result.valor_total,
        cet_mensal=result.cet_mensal,
        criado_em=sim.criado_em,
    )
```

Create `app/routers/cartao.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.enums import TipoSimulacao
from app.repositories.simulacao import create_simulacao
from app.schemas.cartao import CartaoRequest, CartaoResponse
from app.services.cartao import CartaoValidationError, simular_cartao

router = APIRouter(prefix="/api/v1/simulacoes", tags=["cartao"])


@router.post("/cartao", response_model=CartaoResponse, status_code=201)
def criar_simulacao_cartao(
    body: CartaoRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        result = simular_cartao(
            salario=body.salario,
            limite_multiplicador=settings.limite_cartao_multiplicador,
        )
    except CartaoValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    resultado = {
        "margem_cartao": float(result.margem_cartao),
        "limite_credito": float(result.limite_credito),
        "valor_minimo_fatura": float(result.valor_minimo_fatura),
    }

    sim = create_simulacao(
        db=db,
        tipo=TipoSimulacao.CARTAO,
        perfil=body.perfil,
        salario=body.salario,
        input_json=body.model_dump(mode="json"),
        resultado_json=resultado,
    )
    db.commit()

    return CartaoResponse(
        id=sim.id,
        tipo=TipoSimulacao.CARTAO,
        perfil=body.perfil,
        salario=body.salario,
        margem_cartao=result.margem_cartao,
        limite_credito=result.limite_credito,
        valor_minimo_fatura=result.valor_minimo_fatura,
        criado_em=sim.criado_em,
    )
```

Create `app/routers/simulacao.py`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.simulacao import get_simulacao_by_id
from app.schemas.simulacao import SimulacaoDetailResponse

router = APIRouter(prefix="/api/v1/simulacoes", tags=["simulacoes"])


@router.get("/{simulacao_id}", response_model=SimulacaoDetailResponse)
def obter_simulacao(simulacao_id: UUID, db: Session = Depends(get_db)):
    sim = get_simulacao_by_id(db, simulacao_id)
    if sim is None:
        raise HTTPException(status_code=404, detail="Simulacao nao encontrada")
    return SimulacaoDetailResponse(
        id=sim.id,
        tipo=sim.tipo,
        perfil=sim.perfil,
        salario=float(sim.salario),
        input_json=sim.input_json,
        resultado_json=sim.resultado_json,
        criado_em=sim.criado_em.isoformat(),
    )
```

Create `app/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import cartao, emprestimo, health, simulacao


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Amigoz Simulador de Crédito Consignado",
    description="API de simulação de empréstimo consignado e cartão consignado",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(emprestimo.router)
app.include_router(cartao.router)
app.include_router(simulacao.router)
```

Create `app/routers/__init__.py` (empty).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/ -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add app/routers/ app/main.py tests/conftest.py tests/test_api.py
git commit -m "feat: add API routers and integration tests"
```

---

### Task 10: Docker and Docker Compose

**Files:**
- Create: `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`

**Interfaces:**
- Produces: `docker compose up` starts PostgreSQL + API on port 8000

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
```

- [ ] **Step 2: Create entrypoint.sh**

```bash
#!/bin/bash
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: simulador
      POSTGRES_PASSWORD: simulador
      POSTGRES_DB: simulador
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U simulador"]
      interval: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://simulador:simulador@db:5432/simulador
      TAXA_JUROS_MENSAL: "0.0179"
      LIMITE_CARTAO_MULTIPLICADOR: "1.5"
    depends_on:
      db:
        condition: service_healthy
```

- [ ] **Step 4: Verify Docker build**

Run: `docker compose up --build -d`
Expected: API available at `http://localhost:8000/docs`

Run: `docker compose down`

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml entrypoint.sh
git commit -m "feat: add Docker and Docker Compose setup"
```

---

### Task 11: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: CI pipeline running ruff + pytest on push/PR to main

- [ ] **Step 1: Create workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: simulador
          POSTGRES_PASSWORD: simulador
          POSTGRES_DB: simulador
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U simulador"
          --health-interval 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Lint
        run: ruff check .

      - name: Run tests
        env:
          DATABASE_URL: postgresql://simulador:simulador@localhost:5432/simulador
        run: pytest tests/ -v
```

- [ ] **Step 2: Verify locally**

Run: `ruff check .`
Run: `pytest tests/ -v`
Expected: both pass

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions pipeline"
```

---

### Task 12: README

**Files:**
- Create: `README.md`

**Interfaces:**
- Produces: Portuguese README with quick start, margin table, curl examples, CI badge placeholder

- [ ] **Step 1: Write README.md**

Include:
- Project title and description (contexto Amigoz)
- Margin table (CLT/INSS/Servidor)
- Prerequisites (Docker, Docker Compose)
- Quick start: `docker compose up --build`
- curl examples for POST emprestimo, POST cartao, GET simulacao
- Link to `http://localhost:8000/docs`
- CI badge: `![CI](https://github.com/USER/amigoz-simulador/actions/workflows/ci.yml/badge.svg)` (replace USER after GitHub push)
- Tech stack summary

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README in portuguese"
```

---

## Spec Coverage Checklist

| Spec Requirement | Task |
|---|---|
| Empréstimo consignado (Price) | Task 4, 9 |
| Cartão consignado (básico) | Task 5, 9 |
| All profiles CLT/INSS/Servidor | Task 3 |
| PostgreSQL persistence | Task 6, 7 |
| GET /simulacoes/{id} | Task 9 |
| GET /health | Task 9 |
| OpenAPI /docs | Task 9 (FastAPI auto) |
| Docker Compose | Task 10 |
| GitHub Actions CI | Task 11 |
| Unit tests (6 mandatory cases) | Tasks 3–5, 9 |
| README português | Task 12 |
| .env.example | Task 1 |
| Alembic migrations | Task 6 |

## Acceptance Verification

After all tasks, run:

```bash
docker compose up --build -d
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/simulacoes/emprestimo \
  -H "Content-Type: application/json" \
  -d '{"salario":5000,"perfil":"CLT","valor_solicitado":10000,"numero_parcelas":24}'
curl -X POST http://localhost:8000/api/v1/simulacoes/cartao \
  -H "Content-Type: application/json" \
  -d '{"salario":1518,"perfil":"INSS"}'
pytest tests/ -v
ruff check .
```

All must pass before publishing to GitHub.
