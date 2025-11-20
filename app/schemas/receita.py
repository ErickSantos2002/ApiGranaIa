"""
Schemas Pydantic para Receita
"""
from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from dateutil import parser as date_parser


class ReceitaBase(BaseModel):
    """Schema base para Receita"""
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição da receita")
    valor: Decimal = Field(..., gt=0, description="Valor da receita (deve ser maior que zero)")
    categoria: str = Field(..., min_length=1, max_length=100, description="Categoria da receita")
    origem: Optional[str] = Field(None, description="Origem da receita")
    data: Optional[Union[datetime, str]] = Field(None, description="Data da receita (aceita ISO8601, datetime ou string)")

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


class ReceitaCreate(ReceitaBase):
    """Schema para criação de Receita (interno, com usuario)"""
    usuario: str = Field(..., min_length=1, description="RemoteJID do usuário")


class ReceitaCreateRequest(ReceitaBase):
    """Schema para requisição de criação de Receita (sem usuario, vem do token JWT)"""
    pass


class ReceitaUpdate(BaseModel):
    """Schema para atualização de Receita"""
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor: Optional[Decimal] = Field(None, gt=0)
    categoria: Optional[str] = Field(None, min_length=1, max_length=100)
    origem: Optional[str] = Field(None, description="Origem da receita")
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


class ReceitaResponse(ReceitaBase):
    """Schema de resposta para Receita"""
    id: UUID
    usuario: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReceitaListResponse(BaseModel):
    """Schema para lista de receitas"""
    receitas: List[ReceitaResponse]
    total: int

    class Config:
        from_attributes = True


class ReceitaFilter(BaseModel):
    """Schema para filtros de busca de receitas"""
    usuario: Optional[str] = Field(None, description="Filtrar por remotejid do usuário")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    data_inicio: Optional[datetime] = Field(None, description="Data de início do período")
    data_fim: Optional[datetime] = Field(None, description="Data de fim do período")
    valor_min: Optional[Decimal] = Field(None, ge=0, description="Valor mínimo")
    valor_max: Optional[Decimal] = Field(None, ge=0, description="Valor máximo")


class ReceitaCategoriaSummary(BaseModel):
    """Resumo de receitas por categoria"""
    categoria: str
    total: Decimal
    quantidade: int


class ReceitaDashboard(BaseModel):
    """Dashboard de receitas"""
    total_geral: Decimal = Field(default=0, description="Total de receitas")
    quantidade_total: int = Field(default=0, description="Quantidade total de receitas")
    por_categoria: List[ReceitaCategoriaSummary] = Field(default_factory=list, description="Receitas por categoria")
    periodo_inicio: Optional[datetime] = None
    periodo_fim: Optional[datetime] = None

    class Config:
        from_attributes = True
