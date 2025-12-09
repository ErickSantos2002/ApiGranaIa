"""
Rotas para gerenciamento de Gastos Futuros (Cartão de Crédito)
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GastoFuturoService
from app.schemas import (
    GastoFuturoCreate,
    GastoFuturoCreateRequest,
    GastoFuturoUpdate,
    GastoFuturoResponse,
    GastoFuturoDashboard,
    ParcelaResponse,
    MarcarComoPagoRequest,
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)
from app.models.usuario import Usuario
from app.utils.security import get_current_user
from app.utils.premium import require_premium

router = APIRouter(prefix="/gastos-futuros", tags=["Gastos Futuros"])


@router.post(
    "",
    response_model=ResponseModel[GastoFuturoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo gasto futuro",
    description="Cria um novo gasto futuro (cartão de crédito) para o usuário autenticado"
)
async def create_gasto_futuro(
    gasto_futuro_data: GastoFuturoCreateRequest,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo gasto futuro para o usuário autenticado.

    **Requer autenticação via token JWT e premium ativo.**

    - **descricao**: Descrição do gasto futuro (obrigatório)
    - **valor_total**: Valor total do gasto (obrigatório)
    - **categoria**: Categoria do gasto (obrigatório)
    - **data_compra**: Data da compra (opcional, padrão: agora)
    - **data_vencimento**: Data de vencimento do pagamento (obrigatório)
    - **numero_parcelas**: Número de parcelas (padrão: 1 = à vista)
    - **valor_parcela**: Valor de cada parcela (obrigatório se parcelado)
    - **metodo_pagamento**: Método de pagamento (padrão: credito)
    - **observacoes**: Observações adicionais (opcional)

    **Se parcelado (numero_parcelas > 1), as parcelas serão criadas automaticamente!**
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Criando gasto futuro para usuário: {current_user.remotejid}")

    if not current_user.remotejid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui remotejid configurado"
        )

    try:
        # Criar GastoFuturoCreate com o remotejid do usuário autenticado
        gasto_futuro_create = GastoFuturoCreate(
            usuario=current_user.remotejid,
            **gasto_futuro_data.model_dump()
        )

        gasto_futuro = await GastoFuturoService.create(db, gasto_futuro_create)
        await db.commit()

        logger.info(f"Gasto futuro criado com sucesso: {gasto_futuro.id}")

        return ResponseModel(
            success=True,
            message="Gasto futuro criado com sucesso",
            data=GastoFuturoResponse.model_validate(gasto_futuro)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Erro ao criar gasto futuro: {type(e).__name__}: {str(e)}")
        raise


@router.get(
    "",
    response_model=PaginatedResponse[GastoFuturoResponse],
    summary="Listar gastos futuros",
    description="Lista todos os gastos futuros com filtros e paginação"
)
async def list_gastos_futuros(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    usuario: Optional[str] = Query(None, description="Filtrar por remotejid do usuário"),
    status: Optional[str] = Query(None, description="Filtrar por status (ativo, pago, cancelado)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    data_vencimento_inicio: Optional[datetime] = Query(None, description="Data inicial de vencimento"),
    data_vencimento_fim: Optional[datetime] = Query(None, description="Data final de vencimento"),
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista gastos futuros com suporte a filtros e paginação.

    **Filtros disponíveis:**
    - **usuario**: Filtrar por remotejid do usuário
    - **status**: Filtrar por status (ativo, pago, cancelado)
    - **categoria**: Filtrar por categoria
    - **data_vencimento_inicio**: Data inicial de vencimento
    - **data_vencimento_fim**: Data final de vencimento
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    gastos_futuros, total = await GastoFuturoService.list_all(
        db=db,
        skip=pagination.offset,
        limit=pagination.limit,
        usuario=usuario,
        status=status,
        categoria=categoria,
        data_vencimento_inicio=data_vencimento_inicio,
        data_vencimento_fim=data_vencimento_fim,
    )

    gastos_futuros_response = [GastoFuturoResponse.model_validate(g) for g in gastos_futuros]
    meta = create_pagination_meta(page, page_size, total)

    return PaginatedResponse(
        success=True,
        message="Gastos futuros listados com sucesso",
        data=gastos_futuros_response,
        meta=meta
    )


@router.get(
    "/dashboard",
    response_model=ResponseModel[GastoFuturoDashboard],
    summary="Dashboard de gastos futuros",
    description="Retorna resumo e próximos vencimentos de gastos futuros"
)
async def get_gastos_futuros_dashboard(
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna dashboard com estatísticas de gastos futuros do usuário autenticado.

    **Inclui:**
    - Total de gastos futuros ativos
    - Quantidade de gastos vencidos
    - Valor total vencido
    - Gastos do mês atual
    - Próximos vencimentos (7 dias)
    """
    dashboard = await GastoFuturoService.get_dashboard(
        db=db,
        usuario=current_user.remotejid
    )

    return ResponseModel(
        success=True,
        message="Dashboard gerado com sucesso",
        data=dashboard
    )


@router.get(
    "/{gasto_futuro_id}",
    response_model=ResponseModel[GastoFuturoResponse],
    summary="Buscar gasto futuro por ID",
    description="Retorna um gasto futuro específico pelo ID"
)
async def get_gasto_futuro(
    gasto_futuro_id: UUID,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca um gasto futuro específico pelo ID.
    """
    gasto_futuro = await GastoFuturoService.get_by_id(db, gasto_futuro_id)

    return ResponseModel(
        success=True,
        message="Gasto futuro encontrado",
        data=GastoFuturoResponse.model_validate(gasto_futuro)
    )


@router.put(
    "/{gasto_futuro_id}",
    response_model=ResponseModel[GastoFuturoResponse],
    summary="Atualizar gasto futuro",
    description="Atualiza os dados de um gasto futuro"
)
async def update_gasto_futuro(
    gasto_futuro_id: UUID,
    gasto_futuro_data: GastoFuturoUpdate,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de um gasto futuro.

    Apenas os campos fornecidos serão atualizados.
    """
    gasto_futuro = await GastoFuturoService.update(db, gasto_futuro_id, gasto_futuro_data)
    await db.commit()

    return ResponseModel(
        success=True,
        message="Gasto futuro atualizado com sucesso",
        data=GastoFuturoResponse.model_validate(gasto_futuro)
    )


@router.delete(
    "/{gasto_futuro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar gasto futuro",
    description="Remove um gasto futuro e suas parcelas do sistema"
)
async def delete_gasto_futuro(
    gasto_futuro_id: UUID,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um gasto futuro e todas as suas parcelas do sistema.
    """
    await GastoFuturoService.delete(db, gasto_futuro_id)
    await db.commit()


@router.post(
    "/{gasto_futuro_id}/pagar",
    response_model=ResponseModel[GastoFuturoResponse],
    summary="Marcar gasto futuro como pago",
    description="Marca um gasto futuro como pago e opcionalmente cria um gasto normal"
)
async def marcar_gasto_futuro_como_pago(
    gasto_futuro_id: UUID,
    request_data: MarcarComoPagoRequest,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Marca um gasto futuro como pago.

    **Comportamento:**
    - Atualiza status para 'pago'
    - Define data_pagamento
    - Se criar_gasto=true: cria um gasto normal que impacta o saldo

    **Parâmetros:**
    - **data_pagamento**: Data do pagamento (padrão: agora)
    - **criar_gasto**: Se deve criar um gasto normal (padrão: true)
    """
    gasto_futuro = await GastoFuturoService.marcar_como_pago(
        db=db,
        gasto_futuro_id=gasto_futuro_id,
        data_pagamento=request_data.data_pagamento,
        criar_gasto=request_data.criar_gasto
    )
    await db.commit()

    return ResponseModel(
        success=True,
        message="Gasto futuro marcado como pago com sucesso",
        data=GastoFuturoResponse.model_validate(gasto_futuro)
    )


@router.post(
    "/parcelas/{parcela_id}/pagar",
    response_model=ResponseModel[ParcelaResponse],
    summary="Marcar parcela como paga",
    description="Marca uma parcela específica como paga"
)
async def marcar_parcela_como_paga(
    parcela_id: UUID,
    request_data: MarcarComoPagoRequest,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Marca uma parcela específica como paga.

    **Comportamento:**
    - Atualiza status da parcela para 'pago'
    - Define data_pagamento
    - Se criar_gasto=true: cria um gasto normal com o valor da parcela

    **Útil para gastos parcelados onde você paga cada parcela separadamente.**

    **Parâmetros:**
    - **data_pagamento**: Data do pagamento (padrão: agora)
    - **criar_gasto**: Se deve criar um gasto normal (padrão: true)
    """
    parcela = await GastoFuturoService.marcar_parcela_como_paga(
        db=db,
        parcela_id=parcela_id,
        data_pagamento=request_data.data_pagamento,
        criar_gasto=request_data.criar_gasto
    )
    await db.commit()

    return ResponseModel(
        success=True,
        message="Parcela marcada como paga com sucesso",
        data=ParcelaResponse.model_validate(parcela)
    )
