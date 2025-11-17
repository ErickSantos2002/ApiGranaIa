-- Script de inicialização do banco de dados PostgreSQL
-- Executado automaticamente quando o container é criado pela primeira vez

-- Habilitar extensão para gerar UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Habilitar extensão para gerar UUIDs aleatórios (método gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Mensagem de sucesso
SELECT 'Banco de dados inicializado com sucesso!' as status;
