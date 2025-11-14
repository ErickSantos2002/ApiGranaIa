"""
Rotas para gerenciamento de Receitas
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import ReceitaService
from app.schemas import (
    ReceitaCreate,
    ReceitaUpdate,
    ReceitaResponse,
    ReceitaDashboard,
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)

router = APIRouter(prefix="/receitas", tags=["Receitas"])


@router.post(
    "",
    response_model=ResponseModel[ReceitaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova receita",
    description="Cria uma nova receita para um usuário"
)
async def create_receita(
    receita_data: ReceitaCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova receita com os dados fornecidos.

    - **usuario**: ID do usuário (obrigatório)
    - **descricao**: Descrição da receita (obrigatório)
    - **valor**: Valor da receita - deve ser maior que zero (obrigatório)
    - **categoria**: Categoria da receita (obrigatório)
    - **data**: Data da receita (obrigatório)
    """
    receita = await ReceitaService.create(db, receita_data)

    return ResponseModel(
        success=True,
        message="Receita criada com sucesso",
        data=ReceitaResponse.model_validate(receita)
    )


@router.get(
    "",
    response_model=PaginatedResponse[ReceitaResponse],
    summary="Listar receitas",
    description="Lista todas as receitas com filtros e paginação"
)
async def list_receitas(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    usuario_id: Optional[UUID] = Query(None, description="Filtrar por ID do usuário"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início do período"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim do período"),
    valor_min: Optional[Decimal] = Query(None, ge=0, description="Valor mínimo"),
    valor_max: Optional[Decimal] = Query(None, ge=0, description="Valor máximo"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista receitas com suporte a filtros e paginação.

    **Filtros disponíveis:**
    - **usuario_id**: Filtrar por ID do usuário
    - **categoria**: Busca parcial na categoria
    - **data_inicio**: Data de início do período
    - **data_fim**: Data de fim do período
    - **valor_min**: Valor mínimo
    - **valor_max**: Valor máximo
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    receitas, total = await ReceitaService.list_all(
        db=db,
        skip=pagination.offset,
        limit=pagination.limit,
        usuario_id=usuario_id,
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_min=valor_min,
        valor_max=valor_max,
    )

    receitas_response = [ReceitaResponse.model_validate(r) for r in receitas]
    meta = create_pagination_meta(page, page_size, total)

    return PaginatedResponse(
        success=True,
        message="Receitas listadas com sucesso",
        data=receitas_response,
        meta=meta
    )


@router.get(
    "/dashboard",
    response_model=ResponseModel[ReceitaDashboard],
    summary="Dashboard de receitas",
    description="Retorna estatísticas e resumo de receitas"
)
async def get_receitas_dashboard(
    usuario_id: Optional[UUID] = Query(None, description="Filtrar por ID do usuário"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início do período"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim do período"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna dashboard com estatísticas de receitas.

    **Inclui:**
    - Total geral de receitas
    - Quantidade total de registros
    - Receitas agrupadas por categoria (total e quantidade)
    - Período consultado

    **Filtros disponíveis:**
    - **usuario_id**: Filtrar por ID do usuário
    - **data_inicio**: Data de início do período
    - **data_fim**: Data de fim do período
    """
    dashboard = await ReceitaService.get_dashboard(
        db=db,
        usuario_id=usuario_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    return ResponseModel(
        success=True,
        message="Dashboard gerado com sucesso",
        data=dashboard
    )


@router.get(
    "/{receita_id}",
    response_model=ResponseModel[ReceitaResponse],
    summary="Buscar receita por ID",
    description="Retorna uma receita específica pelo ID"
)
async def get_receita(
    receita_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma receita específica pelo ID.
    """
    receita = await ReceitaService.get_by_id(db, receita_id)

    return ResponseModel(
        success=True,
        message="Receita encontrada",
        data=ReceitaResponse.model_validate(receita)
    )


@router.put(
    "/{receita_id}",
    response_model=ResponseModel[ReceitaResponse],
    summary="Atualizar receita",
    description="Atualiza os dados de uma receita"
)
async def update_receita(
    receita_id: UUID,
    receita_data: ReceitaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de uma receita.

    Apenas os campos fornecidos serão atualizados.
    """
    receita = await ReceitaService.update(db, receita_id, receita_data)

    return ResponseModel(
        success=True,
        message="Receita atualizada com sucesso",
        data=ReceitaResponse.model_validate(receita)
    )


@router.delete(
    "/{receita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar receita",
    description="Remove uma receita do sistema"
)
async def delete_receita(
    receita_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta uma receita do sistema.
    """
    await ReceitaService.delete(db, receita_id)
