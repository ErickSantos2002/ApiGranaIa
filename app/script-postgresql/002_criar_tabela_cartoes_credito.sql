-- ============================================
-- Script: 002_criar_tabela_cartoes_credito.sql
-- Descrição: Criação da tabela de Cartões de Crédito e modificação de gastos_futuros
-- Data: 2025-01-09
-- ============================================

-- ============================================
-- 1. CRIAR TABELA DE CARTÕES DE CRÉDITO
-- ============================================

CREATE TABLE IF NOT EXISTS cartoes_credito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario TEXT NOT NULL REFERENCES usuarios(remotejid) ON DELETE CASCADE,
    nome_cartao TEXT NOT NULL CHECK (length(trim(nome_cartao)) >= 2),
    nome_titular TEXT NOT NULL CHECK (length(trim(nome_titular)) >= 3),
    dia_vencimento INTEGER NOT NULL CHECK (dia_vencimento >= 1 AND dia_vencimento <= 31),
    limite NUMERIC(12, 2) NULL CHECK (limite IS NULL OR limite > 0),
    cor TEXT NULL DEFAULT '#3B82F6',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    observacoes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Comentários descritivos
COMMENT ON TABLE cartoes_credito IS 'Tabela de cartões de crédito dos usuários';
COMMENT ON COLUMN cartoes_credito.id IS 'ID único do cartão (UUID)';
COMMENT ON COLUMN cartoes_credito.usuario IS 'RemoteJID do usuário dono do cartão';
COMMENT ON COLUMN cartoes_credito.nome_cartao IS 'Nome/bandeira do cartão (ex: Nubank, Inter, Itaú)';
COMMENT ON COLUMN cartoes_credito.nome_titular IS 'Nome do titular do cartão';
COMMENT ON COLUMN cartoes_credito.dia_vencimento IS 'Dia do mês em que a fatura vence (1-31)';
COMMENT ON COLUMN cartoes_credito.limite IS 'Limite do cartão (opcional)';
COMMENT ON COLUMN cartoes_credito.cor IS 'Cor do cartão para identificação visual (hex)';
COMMENT ON COLUMN cartoes_credito.ativo IS 'Se o cartão está ativo ou cancelado';
COMMENT ON COLUMN cartoes_credito.observacoes IS 'Observações sobre o cartão';
COMMENT ON COLUMN cartoes_credito.created_at IS 'Data de criação do registro';
COMMENT ON COLUMN cartoes_credito.updated_at IS 'Data da última atualização';

-- ============================================
-- 2. CRIAR ÍNDICES PARA CARTÕES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_cartoes_credito_usuario
    ON cartoes_credito(usuario);

CREATE INDEX IF NOT EXISTS idx_cartoes_credito_ativo
    ON cartoes_credito(ativo);

CREATE INDEX IF NOT EXISTS idx_cartoes_credito_usuario_ativo
    ON cartoes_credito(usuario, ativo);

CREATE INDEX IF NOT EXISTS idx_cartoes_credito_dia_vencimento
    ON cartoes_credito(dia_vencimento);

-- ============================================
-- 3. TRIGGER PARA UPDATED_AT
-- ============================================

CREATE OR REPLACE FUNCTION update_cartoes_credito_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cartoes_credito_updated_at
    BEFORE UPDATE ON cartoes_credito
    FOR EACH ROW
    EXECUTE FUNCTION update_cartoes_credito_updated_at();

-- ============================================
-- 4. MODIFICAR TABELA GASTOS_FUTUROS
-- ============================================

-- Adicionar coluna cartao_credito_id
ALTER TABLE gastos_futuros
    ADD COLUMN IF NOT EXISTS cartao_credito_id UUID NULL
    REFERENCES cartoes_credito(id) ON DELETE SET NULL;

-- Comentário
COMMENT ON COLUMN gastos_futuros.cartao_credito_id IS 'ID do cartão de crédito associado (opcional)';

-- Criar índice
CREATE INDEX IF NOT EXISTS idx_gastos_futuros_cartao_credito
    ON gastos_futuros(cartao_credito_id);

CREATE INDEX IF NOT EXISTS idx_gastos_futuros_cartao_status
    ON gastos_futuros(cartao_credito_id, status);

-- ============================================
-- 5. MODIFICAR TABELA GASTOS_FUTUROS_PARCELAS
-- ============================================

-- Adicionar coluna mes_referencia para facilitar consultas de fatura mensal
ALTER TABLE gastos_futuros_parcelas
    ADD COLUMN IF NOT EXISTS mes_referencia TEXT NULL;

-- Comentário
COMMENT ON COLUMN gastos_futuros_parcelas.mes_referencia IS 'Mês de referência no formato YYYY-MM para agrupamento de faturas';

-- Criar índice
CREATE INDEX IF NOT EXISTS idx_parcelas_mes_referencia
    ON gastos_futuros_parcelas(mes_referencia);

-- Popular mes_referencia para registros existentes
UPDATE gastos_futuros_parcelas
SET mes_referencia = TO_CHAR(data_vencimento, 'YYYY-MM')
WHERE mes_referencia IS NULL;

-- ============================================
-- 6. CRIAR VIEW PARA FATURAS MENSAIS
-- ============================================

CREATE OR REPLACE VIEW faturas_mensais AS
SELECT
    gf.cartao_credito_id,
    gfp.mes_referencia,
    cc.nome_cartao,
    cc.dia_vencimento,
    COUNT(DISTINCT gf.id) as total_compras,
    COUNT(gfp.id) as total_parcelas,
    SUM(CASE WHEN gfp.status = 'pendente' THEN gfp.valor_parcela ELSE 0 END) as valor_pendente,
    SUM(CASE WHEN gfp.status = 'pago' THEN gfp.valor_parcela ELSE 0 END) as valor_pago,
    SUM(CASE WHEN gfp.status = 'atrasado' THEN gfp.valor_parcela ELSE 0 END) as valor_atrasado,
    SUM(gfp.valor_parcela) as valor_total_fatura
FROM gastos_futuros gf
INNER JOIN gastos_futuros_parcelas gfp ON gf.id = gfp.gasto_futuro_id
LEFT JOIN cartoes_credito cc ON gf.cartao_credito_id = cc.id
WHERE gf.cartao_credito_id IS NOT NULL
GROUP BY gf.cartao_credito_id, gfp.mes_referencia, cc.nome_cartao, cc.dia_vencimento;

COMMENT ON VIEW faturas_mensais IS 'View com resumo das faturas mensais por cartão de crédito';

-- ============================================
-- 7. CONSTRAINT PARA GARANTIR VENCIMENTO VÁLIDO
-- ============================================

-- Adicionar constraint para garantir que se tem cartao, não precisa data_vencimento manual
ALTER TABLE gastos_futuros
    ADD CONSTRAINT check_vencimento_ou_cartao
    CHECK (
        (cartao_credito_id IS NOT NULL) OR
        (cartao_credito_id IS NULL AND data_vencimento IS NOT NULL)
    );

COMMENT ON CONSTRAINT check_vencimento_ou_cartao ON gastos_futuros IS
    'Garante que ou tem cartão de crédito OU tem data de vencimento manual';

-- ============================================
-- FIM DO SCRIPT
-- ============================================

-- Mensagens de confirmação
DO $$
BEGIN
    RAISE NOTICE '✅ Tabela cartoes_credito criada com sucesso!';
    RAISE NOTICE '✅ Tabela gastos_futuros modificada para referenciar cartões!';
    RAISE NOTICE '✅ Índices e triggers criados!';
    RAISE NOTICE '✅ View faturas_mensais criada!';
    RAISE NOTICE '📋 Sistema de Cartões de Crédito implementado com sucesso!';
END $$;
