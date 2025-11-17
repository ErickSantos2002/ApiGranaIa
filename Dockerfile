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

# Copiar e instalar dependências Python (GLOBALMENTE, sem --user)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM base as runtime

# Copiar dependências instaladas do builder (do site-packages global)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Instalar apenas postgresql-client (necessário em runtime)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar código da aplicação
COPY . .

# Tornar script de inicialização executável
RUN chmod +x start.sh

# Expor porta
EXPOSE 8000

# Health check (simplificado - sem requests que pode não estar disponível)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Comando padrão - usar script de inicialização
CMD ["./start.sh"]
