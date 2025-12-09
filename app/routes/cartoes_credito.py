"""
Rotas para gerenciamento de Cartões de Crédito
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import CartaoCreditoService
from app.schemas import (
    CartaoCreditoCreate,
    CartaoCreditoCreateRequest,
    CartaoCreditoUpdate,
    CartaoCreditoResponse,
    CartaoCreditoComGastos,
    FaturaMensal,
    PagarFaturaRequest,
    ResponseModel,
    PaginatedResponse,
    PaginationParams,
    create_pagination_meta,
)
from app.models.usuario import Usuario
from app.utils.security import get_current_user
from app.utils.premium import require_premium

router = APIRouter(prefix="/cartoes-credito", tags=["Cartões de Crédito"])


@router.post(
    "",
    response_model=ResponseModel[CartaoCreditoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo cartão de crédito",
    description="Cria um novo cartão de crédito para o usuário autenticado"
)
async def create_cartao(
    cartao_data: CartaoCreditoCreateRequest,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo cartão de crédito para o usuário autenticado.

    **Requer autenticação via token JWT e premium ativo.**

    - **nome_cartao**: Nome/bandeira do cartão (ex: Nubank, Inter)
    - **nome_titular**: Nome do titular do cartão
    - **dia_vencimento**: Dia do mês que a fatura vence (1-31)
    - **limite**: Limite do cartão (opcional)
    - **cor**: Cor do cartão em hexadecimal (opcional, padrão: #3B82F6)
    - **ativo**: Se o cartão está ativo (padrão: true)
    - **observacoes**: Observações sobre o cartão (opcional)
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Criando cartão de crédito para usuário: {current_user.remotejid}")

    if not current_user.remotejid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui remotejid configurado"
        )

    try:
        # Criar CartaoCreditoCreate com o remotejid do usuário autenticado
        cartao_create = CartaoCreditoCreate(
            usuario=current_user.remotejid,
            **cartao_data.model_dump()
        )

        cartao = await CartaoCreditoService.create(db, cartao_create)
        await db.commit()

        logger.info(f"Cartão de crédito criado com sucesso: {cartao.id}")

        return ResponseModel(
            success=True,
            message="Cartão de crédito criado com sucesso",
            data=CartaoCreditoResponse.model_validate(cartao)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Erro ao criar cartão de crédito: {type(e).__name__}: {str(e)}")
        raise


@router.get(
    "",
    response_model=PaginatedResponse[CartaoCreditoResponse],
    summary="Listar cartões de crédito",
    description="Lista todos os cartões de crédito com filtros e paginação"
)
async def list_cartoes(
    page: int = Query(default=1, ge=1, description="Número da página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    usuario: Optional[str] = Query(None, description="Filtrar por remotejid do usuário"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista cartões de crédito com suporte a filtros e paginação.

    **Filtros disponíveis:**
    - **usuario**: Filtrar por remotejid do usuário
    - **ativo**: Filtrar por status ativo (true/false)
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    # Se não é admin, força filtro por usuário autenticado
    if usuario is None:
        usuario = current_user.remotejid

    cartoes, total = await CartaoCreditoService.list_all(
        db=db,
        skip=pagination.offset,
        limit=pagination.limit,
        usuario=usuario,
        ativo=ativo,
    )

    cartoes_response = [CartaoCreditoResponse.model_validate(c) for c in cartoes]
    meta = create_pagination_meta(page, page_size, total)

    return PaginatedResponse(
        success=True,
        message="Cartões de crédito listados com sucesso",
        data=cartoes_response,
        meta=meta
    )


@router.get(
    "/{cartao_id}",
    response_model=ResponseModel[CartaoCreditoComGastos],
    summary="Buscar cartão de crédito por ID",
    description="Retorna um cartão de crédito específico com informações de gastos"
)
async def get_cartao(
    cartao_id: UUID,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca um cartão de crédito específico pelo ID com informações adicionais:
    - Total de gastos futuros ativos
    - Valor total pendente
    - Próxima fatura
    """
    cartao = await CartaoCreditoService.get_with_info(db, cartao_id)

    return ResponseModel(
        success=True,
        message="Cartão de crédito encontrado",
        data=cartao
    )


@router.put(
    "/{cartao_id}",
    response_model=ResponseModel[CartaoCreditoResponse],
    summary="Atualizar cartão de crédito",
    description="Atualiza os dados de um cartão de crédito"
)
async def update_cartao(
    cartao_id: UUID,
    cartao_data: CartaoCreditoUpdate,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados de um cartão de crédito.

    Apenas os campos fornecidos serão atualizados.
    """
    cartao = await CartaoCreditoService.update(db, cartao_id, cartao_data)
    await db.commit()

    return ResponseModel(
        success=True,
        message="Cartão de crédito atualizado com sucesso",
        data=CartaoCreditoResponse.model_validate(cartao)
    )


@router.delete(
    "/{cartao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar cartão de crédito",
    description="Remove um cartão de crédito do sistema"
)
async def delete_cartao(
    cartao_id: UUID,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um cartão de crédito do sistema.

    **Atenção:** Os gastos futuros associados terão o cartao_credito_id definido como NULL.
    """
    await CartaoCreditoService.delete(db, cartao_id)
    await db.commit()


@router.get(
    "/{cartao_id}/faturas",
    response_model=ResponseModel[list[FaturaMensal]],
    summary="Listar faturas mensais do cartão",
    description="Retorna as faturas mensais de um cartão de crédito"
)
async def get_faturas(
    cartao_id: UUID,
    mes_inicio: Optional[str] = Query(None, description="Mês inicial (YYYY-MM)"),
    mes_fim: Optional[str] = Query(None, description="Mês final (YYYY-MM)"),
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista as faturas mensais de um cartão de crédito.

    **Parâmetros opcionais:**
    - **mes_inicio**: Filtrar a partir deste mês (formato: YYYY-MM)
    - **mes_fim**: Filtrar até este mês (formato: YYYY-MM)

    **Retorna para cada mês:**
    - Total de compras
    - Total de parcelas
    - Valor pendente
    - Valor pago
    - Valor atrasado
    - Valor total da fatura
    """
    faturas = await CartaoCreditoService.get_faturas_mensais(
        db=db,
        cartao_id=cartao_id,
        mes_inicio=mes_inicio,
        mes_fim=mes_fim
    )

    return ResponseModel(
        success=True,
        message="Faturas listadas com sucesso",
        data=faturas
    )


@router.post(
    "/{cartao_id}/pagar-fatura",
    response_model=ResponseModel[dict],
    summary="Pagar fatura mensal completa",
    description="Paga todas as parcelas pendentes de uma fatura mensal"
)
async def pagar_fatura(
    cartao_id: UUID,
    request_data: PagarFaturaRequest,
    current_user: Usuario = Depends(require_premium),
    db: AsyncSession = Depends(get_db)
):
    """
    Paga todas as parcelas pendentes de uma fatura mensal.

    **Comportamento:**
    - Marca todas as parcelas do mês como 'pago'
    - Define data_pagamento para todas
    - Se criar_gasto=true: cria um gasto único para o valor total da fatura

    **Parâmetros:**
    - **mes_referencia**: Mês da fatura no formato YYYY-MM (ex: 2025-01)
    - **data_pagamento**: Data do pagamento (padrão: agora)
    - **criar_gasto**: Se deve criar um gasto normal (padrão: true)

    **Útil para pagar a fatura completa do cartão de uma vez!**
    """
    resultado = await CartaoCreditoService.pagar_fatura_mensal(
        db=db,
        cartao_id=cartao_id,
        mes_referencia=request_data.mes_referencia,
        data_pagamento=request_data.data_pagamento,
        criar_gasto=request_data.criar_gasto
    )
    await db.commit()

    return ResponseModel(
        success=True,
        message=f"Fatura de {request_data.mes_referencia} paga com sucesso!",
        data=resultado
    )
