FROM python:3.11-slim

RUN pip install --no-cache-dir uv

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY libs/ ./libs/
RUN uv pip install --system --no-cache ./libs

COPY services/gateway/pyproject.toml ./pyproject.toml
RUN uv pip install --system --no-cache .

COPY services/gateway/app/ ./app/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
