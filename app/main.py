from fastapi import FastAPI

from app.routers import emprestimo, cartao, simulacao, health

# Eu crio a aplicação FastAPI e registro os routers principais.
app = FastAPI(title="Amigoz Simulador", version="0.1.0")

# Eu exponho os endpoints da API pública em `/api/v1`.
app.include_router(emprestimo.router, prefix="/api/v1")
app.include_router(cartao.router, prefix="/api/v1")
app.include_router(simulacao.router, prefix="/api/v1")
# Eu mantenho o health sem prefixo para facilitar checks de infra.
app.include_router(health.router)


@app.get("/")
def root():
    # Eu retorno uma mensagem simples indicando que a API está rodando.
    return {"message": "Amigoz Simulador API. See /docs for OpenAPI."}
