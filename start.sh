#!/bin/bash
set -e

echo "🚀 Iniciando Grana IA API..."

# Aguardar banco de dados (opcional, se DATABASE_URL estiver definido)
if [ ! -z "$DATABASE_URL" ]; then
    echo "⏳ Aguardando banco de dados..."
    sleep 3
fi

# Executar migrações (se Alembic estiver configurado)
if [ -f "alembic.ini" ]; then
    echo "📦 Executando migrações..."
    alembic upgrade head || echo "⚠️  Aviso: Erro nas migrações (ou não há migrações)"
fi

# Iniciar servidor
echo "✨ Iniciando servidor Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
