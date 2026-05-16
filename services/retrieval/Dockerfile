FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY libs/ ./libs/
RUN uv pip install --system -e ./libs

RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu

COPY services/retrieval/ ./services/retrieval/
RUN uv pip install --system -e ./services/retrieval

WORKDIR /app/services/retrieval

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
