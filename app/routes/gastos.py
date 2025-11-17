"""
Rotas para gerenciamento de Gastos
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GastoService
from app.schemas import (
    GastoCreate,
    GastoCreateRequest,
    GastoUpdate,
    GastoResponse,
    GastoDashboard,
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)
from app.models.usuario import Usuario
from app.utils.security import get_current_user

router = APIRouter(prefix="/gastos", tags=["Gastos"])


@router.post(
    "/debug",
    summary="Debug - Ver dados enviados",
    description="Endpoint temporário para debug de dados enviados"
)
async def debug_gasto(
    request: dict,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint temporário para debug.
    Mostra exatamente o que está sendo enviado pelo frontend.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"=== DEBUG GASTO ===")
    logger.info(f"Usuário autenticado: {current_user.id} - {current_user.remotejid}")
    logger.info(f"Dados recebidos: {request}")
    logger.info(f"==================")

    return {
        "success": True,
        "user_id": str(current_user.id),
        "user_remotejid": current_user.remotejid,
        "data_received": request
    }


@router.post(
    "",
    response_model=ResponseModel[GastoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo gasto",
    description="Cria um novo gasto para o usuário autenticado"
)
async def create_gasto(
    gasto_data: GastoCreateRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo gasto para o usuário autenticado.

    **Requer autenticação via token JWT.**

    - **descricao**: Descrição do gasto (obrigatório)
    - **valor**: Valor do gasto - deve ser maior que zero (obrigatório)
    - **categoria**: Categoria do gasto (obrigatório)
    - **data**: Data do gasto (opcional, padrão: agora)

    O usuário é automaticamente identificado pelo token JWT.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Log para debug
    logger.info(f"Criando gasto para usuário: {current_user.remotejid}")
    logger.info(f"Dados recebidos: descricao={gasto_data.descricao}, valor={gasto_data.valor}, categoria={gasto_data.categoria}, data={gasto_data.data}")

    # Verificar se o usuário tem remotejid
    if not current_user.remotejid:
        logger.error(f"Usuário {current_user.id} não tem remotejid!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui remotejid configurado"
        )

    try:
        # Criar GastoCreate com o remotejid do usuário autenticado
        gasto_create = GastoCreate(
            usuario=current_user.remotejid,
            descricao=gasto_data.descricao,
            valor=gasto_data.valor,
            categoria=gasto_data.categoria,
            data=gasto_data.data
        )

        logger.info(f"GastoCreate criado: {gasto_create}")

        gasto = await GastoService.create(db, gasto_create)

        logger.info(f"Gasto criado com sucesso: {gasto.id}")

        return ResponseModel(
            success=True,
            message="Gasto criado com sucesso",
            data=GastoResponse.model_validate(gasto)
        )
    except Exception as e:
        logger.error(f"Erro ao criar gasto: {type(e).__name__}: {str(e)}")
        raise


@router.get(
    "",
    response_model=PaginatedResponse[GastoResponse],
    summary="Listar gastos",
    description="Lista todos os gastos com filtros e paginação"
)
async def list_gastos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    usuario: Optional[str] = Query(None, description="Filtrar por remotejid do usuário"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início do período"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim do período"),
    valor_min: Optional[Decimal] = Query(None, ge=0, description="Valor mínimo"),
    valor_max: Optional[Decimal] = Query(None, ge=0, description="Valor máximo"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista gastos com suporte a filtros e paginação.

    **Filtros disponíveis:**
    - **usuario**: Filtrar por remotejid do usuário
    - **categoria**: Busca parcial na categoria
    - **data_inicio**: Data de início do período
    - **data_fim**: Data de fim do período
    - **valor_min**: Valor mínimo
    - **valor_max**: Valor máximo
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    gastos, total = await GastoService.list_all(
        db=db,
        skip=pagination.offset,
        limit=pagination.limit,
        usuario=usuario,
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_min=valor_min,
        valor_max=valor_max,
    )

    gastos_response = [GastoResponse.model_validate(g) for g in gastos]
    meta = create_pagination_meta(page, page_size, total)

    return PaginatedResponse(
        success=True,
        message="Gastos listados com sucesso",
        data=gastos_response,
        meta=meta
    )


@router.get(
    "/dashboard",
    response_model=ResponseModel[GastoDashboard],
    summary="Dashboard de gastos",
    description="Retorna estatísticas e resumo de gastos"
)
async def get_gastos_dashboard(
    usuario: Optional[str] = Query(None, description="Filtrar por remotejid do usuário"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início do período"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim do período"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna dashboard com estatísticas de gastos.

    **Inclui:**
    - Total geral de gastos
    - Quantidade total de registros
    - Gastos agrupados por categoria (total e quantidade)
    - Período consultado

    **Filtros disponíveis:**
    - **usuario**: Filtrar por remotejid do usuário
    - **data_inicio**: Data de início do período
    - **data_fim**: Data de fim do período
    """
    dashboard = await GastoService.get_dashboard(
        db=db,
        usuario=usuario,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    return ResponseModel(
        success=True,
        message="Dashboard gerado com sucesso",
        data=dashboard
    )


@router.get(
    "/{gasto_id}",
    response_model=ResponseModel[GastoResponse],
    summary="Buscar gasto por ID",
    description="Retorna um gasto específico pelo ID"
)
async def get_gasto(
    gasto_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca um gasto específico pelo ID.
    """
    gasto = await GastoService.get_by_id(db, gasto_id)

    return ResponseModel(
        success=True,
        message="Gasto encontrado",
        data=GastoResponse.model_validate(gasto)
    )


@router.put(
    "/{gasto_id}",
    response_model=ResponseModel[GastoResponse],
    summary="Atualizar gasto",
    description="Atualiza os dados de um gasto"
)
async def update_gasto(
    gasto_id: UUID,
    gasto_data: GastoUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de um gasto.

    Apenas os campos fornecidos serão atualizados.
    """
    gasto = await GastoService.update(db, gasto_id, gasto_data)

    return ResponseModel(
        success=True,
        message="Gasto atualizado com sucesso",
        data=GastoResponse.model_validate(gasto)
    )


@router.delete(
    "/{gasto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar gasto",
    description="Remove um gasto do sistema"
)
async def delete_gasto(
    gasto_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um gasto do sistema.
    """
    await GastoService.delete(db, gasto_id)
