FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

RUN pip install uv

COPY src/ ./src/

# Install the library in editable mode
RUN uv pip install --system -e .

# Ensure chroma is available for local vector search via mem0
RUN uv pip install --system chromadb

COPY examples/ ./examples/

RUN mkdir -p /app/chroma_db /app/output

CMD ["python", "examples/docker/demo.py"]
