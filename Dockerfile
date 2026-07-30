FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for building packages and /dev/tcp support
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser || true
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
