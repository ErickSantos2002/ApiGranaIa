"""
Schemas comuns e utilitários
"""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, field_validator


T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """
    Modelo de resposta padrão da API
    """
    success: bool = True
    message: str = "Operação realizada com sucesso"
    data: Optional[T] = None

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """
    Parâmetros de paginação
    """
    page: int = Field(default=1, ge=1, description="Número da página (mínimo 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Itens por página (máximo 100)")

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v):
        if v > 100:
            return 100
        return v

    @property
    def offset(self) -> int:
        """Calcula o offset para a query"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Retorna o limite de itens"""
        return self.page_size


class PaginationMeta(BaseModel):
    """
    Metadados de paginação
    """
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Resposta paginada padrão
    """
    success: bool = True
    message: str = "Operação realizada com sucesso"
    data: List[T] = []
    meta: PaginationMeta

    class Config:
        from_attributes = True


def create_pagination_meta(
    page: int,
    page_size: int,
    total_items: int
) -> PaginationMeta:
    """
    Cria metadados de paginação

    Args:
        page: Página atual
        page_size: Tamanho da página
        total_items: Total de itens

    Returns:
        PaginationMeta: Metadados de paginação
    """
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0

    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
