# Amigoz Simulador

API simples para simular empréstimo consignado e cartão consignado.

Principais objetivos:
- Simular empréstimo usando fórmula Price e validar margem por perfil.
- Simular cartão consignado (margem 5% e limite multiplicador padrão).
- Persistir simulações em PostgreSQL para auditoria.

Regras de negócio principais
- Margem para empréstimo por perfil:
  - `CLT`: 35%
  - `INSS`: 35%
  - `SERVIDOR_PUBLICO`: 40%
- Margem para cartão: 5% do salário
- Limite do cartão: multiplicador padrão `1.5 × salário` (configurável)
- Taxa de juros mensal padrão: `0.0179` (1.79% a.m.) — configurável via `.env`

Quickstart (Docker Compose)

1) Build e sobe a stack (API + Postgres):

```bash
docker-compose up --build
```

2) Variáveis úteis (arquivo `.env` ou env vars):

- `DATABASE_URL` — URL do Postgres (ex: `postgresql://simulador:simulador@db:5432/simulador`)
- `TAXA_JUROS_MENSAL` — taxa padrão (ex: `0.0179`)
- `LIMITE_CARTAO_MULTIPLICADOR` — multiplicador do limite do cartão (ex: `1.5`)

Migrações

```bash
alembic upgrade head
```

Executando testes localmente

```bash
pip install -r requirements-dev.txt
pytest -q
```

Endpoints principais

- POST `/api/v1/simulacoes/emprestimo`
  - Payload exemplo:
    ```json
    {
      "salario": 5000.00,
      "perfil": "CLT",
      "valor_solicitado": 10000.00,
      "numero_parcelas": 24
    }
    ```

- POST `/api/v1/simulacoes/cartao`
  - Payload exemplo:
    ```json
    {
      "salario": 5000.00,
      "perfil": "INSS"
    }
    ```

- GET `/api/v1/simulacoes/{id}` — retorna o `input_json` e `resultado_json` persistidos.

Exemplos cURL

```bash
# Criar empréstimo
curl -s -X POST http://localhost:8000/api/v1/simulacoes/emprestimo \
  -H "Content-Type: application/json" \
  -d '{"salario":5000.00,"perfil":"CLT","valor_solicitado":10000.00,"numero_parcelas":24}'

# Criar cartão
curl -s -X POST http://localhost:8000/api/v1/simulacoes/cartao \
  -H "Content-Type: application/json" \
  -d '{"salario":5000.00,"perfil":"INSS"}'

# Buscar simulação
curl -s http://localhost:8000/api/v1/simulacoes/<id>
```

Documentação interativa

Após subir a API, a documentação OpenAPI está disponível em `/docs`.

Notas de implementação

- Backend: FastAPI + SQLAlchemy 2.0
- Migrations: Alembic (veja `alembic/versions`)
- Testes: `pytest` com SQLite in-memory para fixtures
- CI: GitHub Actions (lint + pytest)

Contribuição

Sinta-se à vontade para abrir issues ou PRs. Se for submeter mudanças que afetam DB structure, atualize as migrations.

---
Arquivo gerado automaticamente pelo assistente de desenvolvimento; se quiser que eu ajuste exemplos, formato ou traduções, diga qual seção modificar.
# Finan-as