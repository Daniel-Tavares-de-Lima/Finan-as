from fastapi import FastAPI

from app.routers import emprestimo, cartao, simulacao, health

app = FastAPI(title="Amigoz Simulador", version="0.1.0")

app.include_router(emprestimo.router, prefix="/api/v1")
app.include_router(cartao.router, prefix="/api/v1")
app.include_router(simulacao.router, prefix="/api/v1")
app.include_router(health.router)


@app.get("/")
def root():
    return {"message": "Amigoz Simulador API. See /docs for OpenAPI."}
