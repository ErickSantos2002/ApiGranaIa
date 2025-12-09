-- =====================================================
-- Script: Criar tabela de Gastos Futuros (Cartão de Crédito)
-- Descrição: Gerencia gastos que ainda não impactaram o saldo
-- Data: 2025-12-09
-- =====================================================

-- Criar ENUM para status de gasto futuro
CREATE TYPE status_gasto_futuro AS ENUM ('ativo', 'pago', 'cancelado');

-- Criar ENUM para método de pagamento
CREATE TYPE metodo_pagamento AS ENUM ('credito', 'debito_futuro', 'parcelado');

-- Criar ENUM para status de parcela
CREATE TYPE status_parcela AS ENUM ('pendente', 'pago', 'atrasado');

-- =====================================================
-- Tabela: gastos_futuros
-- =====================================================
CREATE TABLE IF NOT EXISTS gastos_futuros (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario TEXT NOT NULL REFERENCES usuarios(remotejid) ON DELETE CASCADE,

    -- Informações básicas
    descricao TEXT NOT NULL,
    valor_total NUMERIC(12, 2) NOT NULL CHECK (valor_total > 0),
    categoria categorias_financeiras NOT NULL,

    -- Datas
    data_compra TIMESTAMP NOT NULL DEFAULT NOW(),
    data_vencimento TIMESTAMP NOT NULL,
    data_pagamento TIMESTAMP NULL, -- Quando foi efetivamente pago

    -- Parcelas
    numero_parcelas INTEGER DEFAULT 1 CHECK (numero_parcelas >= 1),
    valor_parcela NUMERIC(12, 2) NULL CHECK (valor_parcela > 0),

    -- Status e método
    status status_gasto_futuro NOT NULL DEFAULT 'ativo',
    metodo_pagamento metodo_pagamento NOT NULL DEFAULT 'credito',

    -- Observações
    observacoes TEXT NULL,

    -- IDs relacionados
    gasto_id UUID NULL, -- ID do gasto criado quando marcar como pago

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_gasto_futuro_usuario FOREIGN KEY (usuario) REFERENCES usuarios(remotejid) ON DELETE CASCADE,
    CONSTRAINT check_valor_parcela_quando_parcelado CHECK (
        (numero_parcelas = 1) OR (numero_parcelas > 1 AND valor_parcela IS NOT NULL)
    )
);

-- =====================================================
-- Tabela: gastos_futuros_parcelas
-- =====================================================
CREATE TABLE IF NOT EXISTS gastos_futuros_parcelas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gasto_futuro_id UUID NOT NULL REFERENCES gastos_futuros(id) ON DELETE CASCADE,

    -- Informações da parcela
    numero_parcela INTEGER NOT NULL CHECK (numero_parcela >= 1),
    total_parcelas INTEGER NOT NULL CHECK (total_parcelas >= 1),
    valor_parcela NUMERIC(12, 2) NOT NULL CHECK (valor_parcela > 0),

    -- Datas
    data_vencimento TIMESTAMP NOT NULL,
    data_pagamento TIMESTAMP NULL,

    -- Status
    status status_parcela NOT NULL DEFAULT 'pendente',

    -- ID do gasto criado quando pagar esta parcela
    gasto_id UUID NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_parcela_gasto_futuro FOREIGN KEY (gasto_futuro_id) REFERENCES gastos_futuros(id) ON DELETE CASCADE,
    CONSTRAINT check_numero_parcela_valido CHECK (numero_parcela <= total_parcelas),
    CONSTRAINT unique_gasto_futuro_parcela UNIQUE (gasto_futuro_id, numero_parcela)
);

-- =====================================================
-- Índices para performance
-- =====================================================

-- Índices na tabela gastos_futuros
CREATE INDEX idx_gastos_futuros_usuario ON gastos_futuros(usuario);
CREATE INDEX idx_gastos_futuros_status ON gastos_futuros(status);
CREATE INDEX idx_gastos_futuros_categoria ON gastos_futuros(categoria);
CREATE INDEX idx_gastos_futuros_data_vencimento ON gastos_futuros(data_vencimento);
CREATE INDEX idx_gastos_futuros_data_compra ON gastos_futuros(data_compra);
CREATE INDEX idx_gastos_futuros_usuario_status ON gastos_futuros(usuario, status);
CREATE INDEX idx_gastos_futuros_usuario_data_vencimento ON gastos_futuros(usuario, data_vencimento);

-- Índices na tabela gastos_futuros_parcelas
CREATE INDEX idx_parcelas_gasto_futuro_id ON gastos_futuros_parcelas(gasto_futuro_id);
CREATE INDEX idx_parcelas_status ON gastos_futuros_parcelas(status);
CREATE INDEX idx_parcelas_data_vencimento ON gastos_futuros_parcelas(data_vencimento);
CREATE INDEX idx_parcelas_gasto_futuro_status ON gastos_futuros_parcelas(gasto_futuro_id, status);

-- =====================================================
-- Trigger para atualizar updated_at automaticamente
-- =====================================================

-- Trigger para gastos_futuros
CREATE OR REPLACE FUNCTION update_gastos_futuros_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_gastos_futuros_updated_at
    BEFORE UPDATE ON gastos_futuros
    FOR EACH ROW
    EXECUTE FUNCTION update_gastos_futuros_updated_at();

-- Trigger para gastos_futuros_parcelas
CREATE OR REPLACE FUNCTION update_parcelas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_parcelas_updated_at
    BEFORE UPDATE ON gastos_futuros_parcelas
    FOR EACH ROW
    EXECUTE FUNCTION update_parcelas_updated_at();

-- =====================================================
-- Comentários nas tabelas para documentação
-- =====================================================

COMMENT ON TABLE gastos_futuros IS 'Gastos futuros que ainda não impactaram o saldo (cartão de crédito, etc)';
COMMENT ON TABLE gastos_futuros_parcelas IS 'Parcelas de gastos futuros parcelados';

COMMENT ON COLUMN gastos_futuros.valor_total IS 'Valor total da compra/gasto';
COMMENT ON COLUMN gastos_futuros.data_compra IS 'Data em que a compra foi realizada';
COMMENT ON COLUMN gastos_futuros.data_vencimento IS 'Data de vencimento do pagamento';
COMMENT ON COLUMN gastos_futuros.data_pagamento IS 'Data em que foi efetivamente pago';
COMMENT ON COLUMN gastos_futuros.gasto_id IS 'ID do gasto normal criado ao marcar como pago';
COMMENT ON COLUMN gastos_futuros.numero_parcelas IS 'Quantidade de parcelas (1 = à vista)';
COMMENT ON COLUMN gastos_futuros.valor_parcela IS 'Valor de cada parcela (quando parcelado)';

COMMENT ON COLUMN gastos_futuros_parcelas.numero_parcela IS 'Número desta parcela (ex: 3 de 12)';
COMMENT ON COLUMN gastos_futuros_parcelas.total_parcelas IS 'Total de parcelas do gasto';
COMMENT ON COLUMN gastos_futuros_parcelas.gasto_id IS 'ID do gasto normal criado ao pagar esta parcela';

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
