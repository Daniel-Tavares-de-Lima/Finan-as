FROM python:3.12-slim

# Eu construo uma imagem leve para a API e instalo dependências do sistema
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalo dependências necessárias para compilação e Postgres client libs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crio um usuário sem senha para rodar o processo em produção.
RUN adduser --disabled-password --gecos "" appuser || true
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
