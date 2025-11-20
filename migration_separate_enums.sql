-- Migration: Separar ENUMs de categorias para gastos e receitas
-- Execute este script no banco de dados PostgreSQL (public schema)
-- Data: 2025-11-20

-- ===========================================================================
-- INÍCIO DA MIGRATION
-- ===========================================================================

BEGIN;

-- 1. Criar novo ENUM para categorias de receitas
CREATE TYPE categorias_receitas AS ENUM (
    'Salário',
    'Freelance',
    'Investimentos',
    'Bonificação',
    'Presente',
    'Aluguel',
    'Venda',
    'Outros'
);

-- 2. Adicionar coluna temporária com o novo ENUM na tabela receitas
ALTER TABLE receitas ADD COLUMN categoria_nova categorias_receitas;

-- 3. Migrar dados existentes para a nova coluna
-- Todas as categorias antigas serão migradas para 'Outros'
-- (ajuste o mapeamento conforme necessário se houver dados que podem ser preservados)
UPDATE receitas
SET categoria_nova = 'Outros'::categorias_receitas;

-- 4. Tornar a nova coluna NOT NULL
ALTER TABLE receitas ALTER COLUMN categoria_nova SET NOT NULL;

-- 5. Remover o índice da coluna antiga
DROP INDEX IF EXISTS idx_receitas_categoria;

-- 6. Remover a coluna antiga
ALTER TABLE receitas DROP COLUMN categoria;

-- 7. Renomear a nova coluna para 'categoria'
ALTER TABLE receitas RENAME COLUMN categoria_nova TO categoria;

-- 8. Recriar o índice na nova coluna
CREATE INDEX idx_receitas_categoria ON receitas(categoria);

-- 9. Criar tabela para rastrear versões do Alembic (se não existir)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- 10. Registrar a versão da migration
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('001');

COMMIT;

-- ===========================================================================
-- FIM DA MIGRATION
-- ===========================================================================

-- NOTA: Após executar este script:
-- 1. Verifique se a migration foi aplicada corretamente:
--    SELECT * FROM alembic_version;
-- 2. Teste criar uma nova receita com categoria 'Salário'
-- 3. Reinicie a API para carregar o novo modelo
