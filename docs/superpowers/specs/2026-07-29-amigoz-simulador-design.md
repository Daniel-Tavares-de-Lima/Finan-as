# Design Spec: Amigoz Simulador de Crédito Consignado

**Data:** 2026-07-29  
**Status:** Aprovado  
**Objetivo:** API de simulação de empréstimo consignado e cartão consignado para demonstração técnica e visão de negócio (Amigoz).

---

## 1. Contexto e Objetivo

Projeto open-source no GitHub que simula produtos de crédito consignado alinhados ao portfólio Amigoz:

- **Empréstimo consignado** — parcelas fixas descontadas em folha (sistema Price)
- **Cartão consignado** — margem para desconto do mínimo da fatura + limite de crédito

A API deve estar documentada (OpenAPI/Swagger), persistir simulações no PostgreSQL, incluir testes unitários e CI no GitHub Actions.

---

## 2. Decisões de Escopo

| Decisão | Escolha |
|---|---|
| Produtos | Empréstimo consignado + Cartão consignado |
| Perfis suportados | CLT, INSS, Servidor Público |
| Framework | FastAPI |
| Margem comprometida | Não — assume 100% da margem livre |
| Taxa de juros (empréstimo) | Fixa, configurável via variável de ambiente |
| Sistema de amortização | Tabela Price (parcelas fixas) |
| Cartão consignado | Básico: margem 5%, limite 1,5× salário, mínimo da fatura |
| Persistência | Histórico de simulações (sem cadastro de usuário) |
| Infraestrutura | Docker Compose (PostgreSQL + API) |
| CI | GitHub Actions com pytest |

---

## 3. Arquitetura

### 3.1 Abordagem escolhida: Monolito em camadas

```
routers → services → repositories → models
```

Um serviço centralizado de margem consignável (`services/margem.py`) concentra as regras por perfil. Escolhido por equilibrar simplicidade, testabilidade e clareza para revisores de código.

### 3.2 Estrutura do projeto

```
amigoz-simulador/
├── app/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── config.py                # Settings (taxa, limite cartão, DB)
│   ├── routers/
│   │   ├── emprestimo.py        # POST /simulacoes/emprestimo
│   │   └── cartao.py            # POST /simulacoes/cartao
│   ├── services/
│   │   ├── margem.py            # Regras por perfil
│   │   ├── emprestimo.py        # Cálculo Price
│   │   └── cartao.py            # Limite + mínimo fatura
│   ├── repositories/
│   │   └── simulacao.py         # CRUD PostgreSQL
│   ├── models/
│   │   └── simulacao.py         # SQLAlchemy models
│   └── schemas/
│       ├── emprestimo.py        # Pydantic request/response
│       └── cartao.py
├── tests/
│   ├── conftest.py              # Fixtures (DB de teste, client)
│   ├── test_margem.py
│   ├── test_emprestimo.py
│   ├── test_cartao.py
│   └── test_api.py
├── alembic/                     # Migrations
├── docker-compose.yml
├── Dockerfile
├── .github/workflows/ci.yml
├── requirements.txt
├── .env.example
└── README.md
```

### 3.3 Stack tecnológica

| Componente | Tecnologia |
|---|---|
| API | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validação | Pydantic v2 |
| Banco | PostgreSQL 16 |
| Testes | pytest, httpx, pytest-asyncio |
| Lint | ruff |
| Container | Docker + Docker Compose |
| CI | GitHub Actions |

---

## 4. Regras de Negócio

### 4.1 Margem consignável por perfil

| Perfil | Margem empréstimo | Margem cartão | Total |
|---|---|---|---|
| INSS | 35% | 5% | 45% |
| CLT | 35% | 5% | 40% |
| Servidor Público | 40% | 5% | 45% |

Referência legal: Lei nº 10.820/2003, Lei nº 14.431/2022 (INSS), Lei nº 14.509/2022 (servidores).

### 4.2 Empréstimo consignado

**Entradas:** salário, perfil, valor solicitado, número de parcelas.

**Cálculos:**

```
margem_disponivel = salario × percentual_emprestimo(perfil)
valor_maximo_parcela = margem_disponivel
PMT = PV × [i × (1+i)^n] / [(1+i)^n - 1]    # Tabela Price
valor_total = PMT × n
```

- `i` = taxa mensal (`TAXA_JUROS_MENSAL`, default `0.0179` = 1,79% a.m.)
- `PV` = valor solicitado
- `n` = número de parcelas

**Validações:**

- `salario > 0`
- `valor_solicitado > 0`
- `1 <= numero_parcelas <= 96`
- `PMT <= margem_disponivel` — rejeitar com HTTP 422 se parcela exceder margem
- `perfil` deve ser enum válido

**CET mensal:** igual à taxa de juros mensal (sem IOF/tarifas nesta simulação simplificada).

### 4.3 Cartão consignado

**Entradas:** salário, perfil.

**Cálculos:**

```
margem_cartao = salario × 0.05
limite_credito = salario × LIMITE_CARTAO_MULTIPLICADOR    # default 1.5
valor_minimo_fatura = margem_cartao
```

**Validações:**

- `salario > 0`
- `perfil` deve ser enum válido

O perfil afeta apenas a exibição contextual (margem total do tomador); a margem do cartão é sempre 5% do salário.

### 4.4 Margem comprometida

Fora de escopo nesta versão. A API assume margem 100% disponível.

---

## 5. API — Endpoints

Base path: `/api/v1`

### 5.1 POST `/simulacoes/emprestimo`

Simula empréstimo consignado e persiste resultado.

**Request body:**

```json
{
  "salario": 5000.00,
  "perfil": "CLT",
  "valor_solicitado": 10000.00,
  "numero_parcelas": 24
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tipo": "EMPRESTIMO",
  "perfil": "CLT",
  "salario": 5000.00,
  "margem_disponivel": 1750.00,
  "valor_solicitado": 10000.00,
  "numero_parcelas": 24,
  "taxa_juros_mensal": 0.0179,
  "valor_parcela": 512.34,
  "valor_total": 12296.16,
  "cet_mensal": 0.0179,
  "criado_em": "2026-07-29T23:00:00Z"
}
```

**Erros:**

- `422` — validação falhou (parcela excede margem, campos inválidos)
- `422` — perfil inválido

### 5.2 POST `/simulacoes/cartao`

Simula cartão consignado e persiste resultado.

**Request body:**

```json
{
  "salario": 5000.00,
  "perfil": "INSS"
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "tipo": "CARTAO",
  "perfil": "INSS",
  "salario": 5000.00,
  "margem_cartao": 250.00,
  "limite_credito": 7500.00,
  "valor_minimo_fatura": 250.00,
  "criado_em": "2026-07-29T23:00:00Z"
}
```

### 5.3 GET `/simulacoes/{id}`

Retorna simulação persistida por UUID.

**Response (200):** objeto completo da simulação (empréstimo ou cartão).

**Erros:**

- `404` — simulação não encontrada

### 5.4 GET `/health`

Health check para Docker e monitoramento.

**Response (200):**

```json
{
  "status": "ok",
  "database": "connected"
}
```

### 5.5 Documentação

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

---

## 6. Banco de Dados

### 6.1 Tabela `simulacoes`

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | UUID | PK, gerado na aplicação |
| `tipo` | VARCHAR(20) | `EMPRESTIMO` ou `CARTAO` |
| `perfil` | VARCHAR(30) | `CLT`, `INSS`, `SERVIDOR_PUBLICO` |
| `salario` | NUMERIC(12,2) | Salário informado |
| `input_json` | JSONB | Payload original do request |
| `resultado_json` | JSONB | Resultado completo da simulação |
| `criado_em` | TIMESTAMPTZ | Timestamp de criação (UTC) |

Índice em `criado_em` para consultas futuras por período.

### 6.2 Migrations

Alembic com migration inicial criando a tabela `simulacoes`.

---

## 7. Configuração

Variáveis de ambiente (`.env.example`):

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@db:5432/simulador` | Connection string |
| `TAXA_JUROS_MENSAL` | `0.0179` | Taxa mensal empréstimo (1,79%) |
| `LIMITE_CARTAO_MULTIPLICADOR` | `1.5` | Multiplicador do limite do cartão |
| `APP_ENV` | `development` | Ambiente da aplicação |

---

## 8. Testes

### 8.1 Testes unitários

| Arquivo | Cobertura |
|---|---|
| `test_margem.py` | Percentuais corretos para CLT, INSS, Servidor Público |
| `test_emprestimo.py` | Fórmula Price, validação parcela > margem, limites de parcelas |
| `test_cartao.py` | Cálculo de limite (1,5×) e mínimo da fatura (5%) |
| `test_api.py` | Endpoints via TestClient, persistência, 404, 422 |

### 8.2 Fixtures

- Banco PostgreSQL de teste (via Docker ou override de `DATABASE_URL`)
- `TestClient` do FastAPI com override de dependências

### 8.3 Casos de teste obrigatórios

1. CLT com salário R$ 5.000 → margem empréstimo R$ 1.750 (35%)
2. INSS com salário R$ 1.518 → margem cartão R$ 75,90 (5%)
3. Servidor Público com salário R$ 8.000 → margem empréstimo R$ 3.200 (40%)
4. Empréstimo rejeitado quando parcela excede margem
5. Simulação persistida e recuperável via GET
6. GET com UUID inexistente retorna 404

---

## 9. Infraestrutura

### 9.1 Docker Compose

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
    depends_on:
      db:
        condition: service_healthy
```

Comando de startup: aguardar DB, rodar migrations Alembic, iniciar uvicorn.

### 9.2 GitHub Actions CI

Pipeline em `.github/workflows/ci.yml`:

1. Trigger: push e pull_request na branch `main`
2. Setup Python 3.12
3. Instalar dependências
4. Ruff lint
5. pytest com PostgreSQL service container
6. Badge de status no README

---

## 10. README

O README deve conter:

- Descrição do projeto e contexto Amigoz
- Regras de margem consignável (tabela resumida)
- Quick start com Docker Compose
- Exemplos de curl para cada endpoint
- Link para `/docs`
- Badge do CI

Idioma: **português**.

---

## 11. Fora de Escopo (v1)

- Autenticação/autorização
- Margem comprometida / contratos existentes
- Cartão benefício consignado (5% adicional INSS)
- Parcelamento de fatura do cartão
- Saque do cartão (70% do limite)
- IOF, tarifas, seguro prestamista
- CET anualizado
- Listagem paginada de simulações
- Deploy em produção (AWS, etc.)

---

## 12. Critérios de Aceite

- [ ] `docker compose up` sobe API e PostgreSQL funcional
- [ ] POST empréstimo e cartão retornam cálculos corretos e persistem no banco
- [ ] GET por ID recupera simulação salva
- [ ] `/docs` exibe documentação OpenAPI completa
- [ ] Todos os testes passam localmente e no CI
- [ ] README em português com exemplos de uso
- [ ] Repositório publicado no GitHub
