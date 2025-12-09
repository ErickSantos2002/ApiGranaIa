"""
Schemas Pydantic para Gasto Futuro (Cartão de Crédito)
"""
from datetime import datetime
from typing import Optional, List, Union, Literal
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from dateutil import parser as date_parser


# ========== Schemas para Parcelas ==========

class ParcelaBase(BaseModel):
    """Schema base para Parcela"""
    numero_parcela: int = Field(..., ge=1, description="Número da parcela")
    total_parcelas: int = Field(..., ge=1, description="Total de parcelas")
    valor_parcela: Decimal = Field(..., gt=0, description="Valor da parcela")
    data_vencimento: Union[datetime, str] = Field(..., description="Data de vencimento da parcela")
    status: Literal['pendente', 'pago', 'atrasado'] = Field(default='pendente', description="Status da parcela")

    @field_validator("data_vencimento", mode="before")
    @classmethod
    def validate_data_vencimento(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Formato de data inválido: {v}")
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")

    @model_validator(mode="after")
    def validate_numero_parcela(self):
        if self.numero_parcela > self.total_parcelas:
            raise ValueError("Número da parcela não pode ser maior que o total de parcelas")
        return self


class ParcelaCreate(ParcelaBase):
    """Schema para criação de Parcela"""
    gasto_futuro_id: UUID = Field(..., description="ID do gasto futuro")


class ParcelaUpdate(BaseModel):
    """Schema para atualização de Parcela"""
    data_vencimento: Optional[Union[datetime, str]] = None
    data_pagamento: Optional[Union[datetime, str]] = None
    status: Optional[Literal['pendente', 'pago', 'atrasado']] = None
    gasto_id: Optional[UUID] = Field(None, description="ID do gasto criado ao pagar")

    @field_validator("data_vencimento", "data_pagamento", mode="before")
    @classmethod
    def validate_data(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v)
            except (ValueError, TypeError):
                raise ValueError(f"Formato de data inválido: {v}")
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")


class ParcelaResponse(ParcelaBase):
    """Schema de resposta para Parcela"""
    id: UUID
    gasto_futuro_id: UUID
    data_pagamento: Optional[datetime] = None
    gasto_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Schemas para Gasto Futuro ==========

class GastoFuturoBase(BaseModel):
    """Schema base para Gasto Futuro"""
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição do gasto futuro")
    valor_total: Decimal = Field(..., gt=0, description="Valor total do gasto")
    categoria: str = Field(..., min_length=1, max_length=100, description="Categoria do gasto")
    data_compra: Optional[Union[datetime, str]] = Field(None, description="Data da compra")
    data_vencimento: Optional[Union[datetime, str]] = Field(None, description="Data de vencimento (opcional se tiver cartão)")
    cartao_credito_id: Optional[UUID] = Field(None, description="ID do cartão de crédito (opcional)")
    numero_parcelas: int = Field(default=1, ge=1, description="Número de parcelas (1 = à vista)")
    valor_parcela: Optional[Decimal] = Field(None, gt=0, description="Valor de cada parcela")
    metodo_pagamento: Literal['credito', 'debito_futuro', 'parcelado'] = Field(
        default='credito',
        description="Método de pagamento"
    )
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações adicionais")

    @field_validator("data_compra", "data_vencimento", mode="before")
    @classmethod
    def validate_data(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v)
            except (ValueError, TypeError):
                raise ValueError(f"Formato de data inválido: {v}")
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")

    @field_validator("valor_total", "valor_parcela")
    @classmethod
    def validate_valor(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return round(v, 2) if v else v

    @field_validator("descricao", "categoria")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_parcelas(self):
        """Valida se valor_parcela está definido quando parcelado"""
        if self.numero_parcelas > 1 and self.valor_parcela is None:
            raise ValueError("valor_parcela é obrigatório quando numero_parcelas > 1")
        if self.numero_parcelas > 1 and self.metodo_pagamento != 'parcelado':
            self.metodo_pagamento = 'parcelado'
        return self

    @model_validator(mode="after")
    def validate_cartao_ou_vencimento(self):
        """Valida que cartao_credito_id OU data_vencimento deve ser fornecido"""
        if self.cartao_credito_id is None and self.data_vencimento is None:
            raise ValueError("Deve fornecer cartao_credito_id OU data_vencimento")
        return self


class GastoFuturoCreate(GastoFuturoBase):
    """Schema para criação de Gasto Futuro (interno, com usuario)"""
    usuario: str = Field(..., min_length=1, description="RemoteJID do usuário")
    status: Literal['ativo', 'pago', 'cancelado'] = Field(default='ativo', description="Status do gasto")


class GastoFuturoCreateRequest(GastoFuturoBase):
    """Schema para requisição de criação de Gasto Futuro (sem usuario, vem do token JWT)"""
    pass


class GastoFuturoUpdate(BaseModel):
    """Schema para atualização de Gasto Futuro"""
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor_total: Optional[Decimal] = Field(None, gt=0)
    categoria: Optional[str] = Field(None, min_length=1, max_length=100)
    data_compra: Optional[Union[datetime, str]] = None
    data_vencimento: Optional[Union[datetime, str]] = None
    data_pagamento: Optional[Union[datetime, str]] = None
    numero_parcelas: Optional[int] = Field(None, ge=1)
    valor_parcela: Optional[Decimal] = Field(None, gt=0)
    status: Optional[Literal['ativo', 'pago', 'cancelado']] = None
    metodo_pagamento: Optional[Literal['credito', 'debito_futuro', 'parcelado']] = None
    observacoes: Optional[str] = Field(None, max_length=1000)
    gasto_id: Optional[UUID] = Field(None, description="ID do gasto criado ao pagar")

    @field_validator("data_compra", "data_vencimento", "data_pagamento", mode="before")
    @classmethod
    def validate_data(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v)
            except (ValueError, TypeError):
                raise ValueError(f"Formato de data inválido: {v}")
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")

    @field_validator("valor_total", "valor_parcela")
    @classmethod
    def validate_valor(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return round(v, 2) if v else v

    @field_validator("descricao", "categoria")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip() if v else v


class GastoFuturoResponse(GastoFuturoBase):
    """Schema de resposta para Gasto Futuro"""
    id: UUID
    usuario: str
    status: Literal['ativo', 'pago', 'cancelado']
    data_pagamento: Optional[datetime] = None
    gasto_id: Optional[UUID] = None
    parcelas: List[ParcelaResponse] = Field(default_factory=list, description="Lista de parcelas")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Schemas para Dashboard e Resumos ==========

class GastoFuturoResumo(BaseModel):
    """Resumo de gastos futuros"""
    total_valor: Decimal = Field(default=0, description="Valor total de gastos futuros ativos")
    quantidade_total: int = Field(default=0, description="Quantidade total de gastos futuros")
    quantidade_vencidos: int = Field(default=0, description="Quantidade de gastos vencidos")
    valor_vencido: Decimal = Field(default=0, description="Valor total vencido")
    quantidade_mes_atual: int = Field(default=0, description="Quantidade com vencimento no mês atual")
    valor_mes_atual: Decimal = Field(default=0, description="Valor com vencimento no mês atual")


class GastoFuturoProximosVencimentos(BaseModel):
    """Gastos futuros com vencimento próximo"""
    id: UUID
    descricao: str
    valor_total: Decimal
    data_vencimento: datetime
    dias_para_vencimento: int
    status: str


class GastoFuturoDashboard(BaseModel):
    """Dashboard de gastos futuros"""
    resumo: GastoFuturoResumo
    proximos_vencimentos: List[GastoFuturoProximosVencimentos] = Field(
        default_factory=list,
        description="Próximos vencimentos (7 dias)"
    )

    class Config:
        from_attributes = True


# ========== Request para Marcar como Pago ==========

class MarcarComoPagoRequest(BaseModel):
    """Request para marcar gasto futuro ou parcela como pago"""
    data_pagamento: Optional[Union[datetime, str]] = Field(
        None,
        description="Data do pagamento (padrão: agora)"
    )
    criar_gasto: bool = Field(
        default=True,
        description="Se deve criar um gasto normal ao marcar como pago"
    )

    @field_validator("data_pagamento", mode="before")
    @classmethod
    def validate_data_pagamento(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v)
            except (ValueError, TypeError):
                raise ValueError(f"Formato de data inválido: {v}")
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")
