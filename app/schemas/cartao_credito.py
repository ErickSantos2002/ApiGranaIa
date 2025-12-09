"""
Schemas Pydantic para Cartão de Crédito
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class CartaoCreditoBase(BaseModel):
    """Schema base para Cartão de Crédito"""
    nome_cartao: str = Field(..., min_length=2, max_length=100, description="Nome/bandeira do cartão")
    nome_titular: str = Field(..., min_length=3, max_length=200, description="Nome do titular do cartão")
    dia_vencimento: int = Field(..., ge=1, le=31, description="Dia do mês que a fatura vence")
    limite: Optional[Decimal] = Field(None, gt=0, description="Limite do cartão (opcional)")
    cor: Optional[str] = Field("#3B82F6", max_length=7, description="Cor do cartão em hexadecimal")
    ativo: bool = Field(True, description="Se o cartão está ativo")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações sobre o cartão")

    @field_validator("nome_cartao", "nome_titular")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip() if v else v

    @field_validator("limite")
    @classmethod
    def validate_limite(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Limite deve ser maior que zero")
        return round(v, 2) if v else v

    @field_validator("cor")
    @classmethod
    def validate_cor(cls, v):
        if v and not v.startswith("#"):
            raise ValueError("Cor deve estar no formato hexadecimal (#RRGGBB)")
        if v and len(v) != 7:
            raise ValueError("Cor deve ter 7 caracteres (#RRGGBB)")
        return v


class CartaoCreditoCreate(CartaoCreditoBase):
    """Schema para criação de Cartão de Crédito (interno, com usuario)"""
    usuario: str = Field(..., min_length=1, description="RemoteJID do usuário")


class CartaoCreditoCreateRequest(CartaoCreditoBase):
    """Schema para requisição de criação de Cartão de Crédito (sem usuario, vem do token JWT)"""
    pass


class CartaoCreditoUpdate(BaseModel):
    """Schema para atualização de Cartão de Crédito"""
    nome_cartao: Optional[str] = Field(None, min_length=2, max_length=100)
    nome_titular: Optional[str] = Field(None, min_length=3, max_length=200)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=31)
    limite: Optional[Decimal] = Field(None, gt=0)
    cor: Optional[str] = Field(None, max_length=7)
    ativo: Optional[bool] = None
    observacoes: Optional[str] = Field(None, max_length=1000)

    @field_validator("nome_cartao", "nome_titular")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip() if v else v

    @field_validator("limite")
    @classmethod
    def validate_limite(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Limite deve ser maior que zero")
        return round(v, 2) if v else v

    @field_validator("cor")
    @classmethod
    def validate_cor(cls, v):
        if v and not v.startswith("#"):
            raise ValueError("Cor deve estar no formato hexadecimal (#RRGGBB)")
        if v and len(v) != 7:
            raise ValueError("Cor deve ter 7 caracteres (#RRGGBB)")
        return v


class CartaoCreditoResponse(CartaoCreditoBase):
    """Schema de resposta para Cartão de Crédito"""
    id: UUID
    usuario: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartaoCreditoComGastos(CartaoCreditoResponse):
    """Schema de resposta com informações de gastos do cartão"""
    total_gastos_ativos: int = Field(0, description="Total de gastos futuros ativos")
    valor_total_pendente: Decimal = Field(0, description="Valor total pendente de pagamento")
    proxima_fatura: Optional[str] = Field(None, description="Mês da próxima fatura (YYYY-MM)")

    class Config:
        from_attributes = True


class FaturaMensal(BaseModel):
    """Schema para fatura mensal de um cartão"""
    cartao_id: UUID
    nome_cartao: str
    mes_referencia: str = Field(..., description="Mês de referência (YYYY-MM)")
    dia_vencimento: int
    total_compras: int = Field(0, description="Total de compras no mês")
    total_parcelas: int = Field(0, description="Total de parcelas no mês")
    valor_pendente: Decimal = Field(0, description="Valor pendente de pagamento")
    valor_pago: Decimal = Field(0, description="Valor já pago")
    valor_atrasado: Decimal = Field(0, description="Valor atrasado")
    valor_total_fatura: Decimal = Field(0, description="Valor total da fatura")


class PagarFaturaRequest(BaseModel):
    """Request para pagar fatura completa de um cartão"""
    mes_referencia: str = Field(..., description="Mês de referência da fatura (YYYY-MM)")
    data_pagamento: Optional[datetime] = Field(None, description="Data do pagamento (padrão: agora)")
    criar_gasto: bool = Field(True, description="Se deve criar um gasto normal")

    @field_validator("mes_referencia")
    @classmethod
    def validate_mes_referencia(cls, v):
        import re
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError("Formato inválido. Use YYYY-MM (ex: 2025-01)")
        return v
