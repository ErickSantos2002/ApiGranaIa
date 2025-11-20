"""
Schemas Pydantic para Gasto
"""
from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from dateutil import parser as date_parser


class GastoBase(BaseModel):
    """Schema base para Gasto"""
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição do gasto")
    valor: Decimal = Field(..., gt=0, description="Valor do gasto (deve ser maior que zero)")
    categoria: str = Field(..., min_length=1, max_length=100, description="Categoria do gasto")
    data: Optional[Union[datetime, str]] = Field(None, description="Data do gasto (aceita ISO8601, datetime ou string)")

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, v):
        """
        Valida e converte o campo data para datetime.
        Aceita datetime, string ISO8601, ou outros formatos comuns.
        """
        if v is None:
            return None

        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            try:
                # Usar dateutil.parser que aceita vários formatos
                return date_parser.parse(v)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Formato de data inválido: {v}. Use ISO8601 (ex: 2025-11-17T12:00:00) ou outro formato padrão.")

        # Se não for datetime nem string, tentar converter
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        # Limita a 2 casas decimais
        return round(v, 2)

    @field_validator("descricao", "categoria")
    @classmethod
    def validate_not_empty(cls, v):
        if len(v.strip()) == 0:
            raise ValueError("Campo não pode ser vazio")
        return v.strip()


class GastoCreate(GastoBase):
    """Schema para criação de Gasto (interno, com usuario)"""
    usuario: str = Field(..., min_length=1, description="RemoteJID do usuário")


class GastoCreateRequest(GastoBase):
    """Schema para requisição de criação de Gasto (sem usuario, vem do token JWT)"""
    pass


class GastoUpdate(BaseModel):
    """Schema para atualização de Gasto"""
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor: Optional[Decimal] = Field(None, gt=0)
    categoria: Optional[str] = Field(None, min_length=1, max_length=100)
    data: Optional[Union[datetime, str]] = None

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, v):
        """
        Valida e converte o campo data para datetime.
        Aceita datetime, string ISO8601, ou outros formatos comuns.
        """
        if v is None:
            return None

        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            try:
                # Usar dateutil.parser que aceita vários formatos
                return date_parser.parse(v)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Formato de data inválido: {v}. Use ISO8601 (ex: 2025-11-17T12:00:00) ou outro formato padrão.")

        # Se não for datetime nem string, tentar converter
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError(f"Formato de data inválido: {v}")

    @field_validator("valor")
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


class GastoResponse(GastoBase):
    """Schema de resposta para Gasto"""
    id: UUID
    usuario: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GastoListResponse(BaseModel):
    """Schema para lista de gastos"""
    gastos: List[GastoResponse]
    total: int

    class Config:
        from_attributes = True


class GastoFilter(BaseModel):
    """Schema para filtros de busca de gastos"""
    usuario: Optional[str] = Field(None, description="Filtrar por remotejid do usuário")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    data_inicio: Optional[datetime] = Field(None, description="Data de início do período")
    data_fim: Optional[datetime] = Field(None, description="Data de fim do período")
    valor_min: Optional[Decimal] = Field(None, ge=0, description="Valor mínimo")
    valor_max: Optional[Decimal] = Field(None, ge=0, description="Valor máximo")


class GastoCategoriaSummary(BaseModel):
    """Resumo de gastos por categoria"""
    categoria: str
    total: Decimal
    quantidade: int


class GastoDashboard(BaseModel):
    """Dashboard de gastos"""
    total_geral: Decimal = Field(default=0, description="Total de gastos")
    quantidade_total: int = Field(default=0, description="Quantidade total de gastos")
    por_categoria: List[GastoCategoriaSummary] = Field(default_factory=list, description="Gastos por categoria")
    periodo_inicio: Optional[datetime] = None
    periodo_fim: Optional[datetime] = None

    class Config:
        from_attributes = True
