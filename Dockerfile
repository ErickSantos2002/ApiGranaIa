# Stage 1: Base
FROM python:3.11-slim as base

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Stage 2: Builder
FROM base as builder

# Instalar dependências do sistema necessárias para compilar pacotes
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 3: Runtime
FROM base as runtime

# Copiar dependências instaladas do builder
COPY --from=builder /root/.local /root/.local

# Adicionar .local/bin ao PATH
ENV PATH=/root/.local/bin:$PATH

# Instalar apenas postgresql-client (necessário em runtime)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
