FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY libs/ ./libs/
RUN uv pip install --system --no-cache ./libs

COPY services/ingestion/pyproject.toml ./pyproject.toml
RUN uv pip install --system --no-cache .

COPY services/ingestion/app/ ./app/
COPY services/ingestion/alembic/ ./alembic/
COPY services/ingestion/alembic.ini ./alembic.ini

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
